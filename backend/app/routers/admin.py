from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.bookmark import Bookmark
from app.models.company import Company
from app.models.role import Role
from app.models.experience import Experience
from app.models.question import Question
from app.models.round import RecruitmentRound
from app.matching import similarity
from app.schemas.company_schemas import MergeCompaniesIn
from app.security import role_required
from app.user_cleanup import delete_user_account

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/statistics")
def platform_statistics(
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    """Admin-only. Platform-wide counts via plain SQL aggregation."""
    total_students = db.query(User).filter_by(role="student").count()
    total_alumni = db.query(User).filter_by(role="alumni").count()
    total_companies = db.query(Company).count()
    total_experiences = db.query(Experience).filter_by(status="approved").count()
    pending_experiences = db.query(Experience).filter_by(status="pending").count()

    most_discussed = (
        db.query(Company.name, func.count(Experience.id).label("count"))
        .join(Experience, Experience.company_id == Company.id)
        .filter(Experience.status == "approved")
        .group_by(Company.id)
        .order_by(func.count(Experience.id).desc())
        .limit(5)
        .all()
    )

    most_frequent_topics = (
        db.query(func.min(Question.topic).label("topic"), func.count(Question.id).label("count"))
        .join(RecruitmentRound, Question.round_id == RecruitmentRound.id)
        .join(Experience, RecruitmentRound.experience_id == Experience.id)
        .filter(Experience.status == "approved", Question.topic.isnot(None), Question.topic != "")
        .group_by(func.lower(Question.topic))
        .order_by(func.count(Question.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_students": total_students,
        "total_alumni": total_alumni,
        "total_companies": total_companies,
        "total_experiences": total_experiences,
        "pending_experiences": pending_experiences,
        "most_discussed_companies": [{"company": name, "count": count} for name, count in most_discussed],
        "most_frequent_topics": [{"topic": topic, "count": count} for topic, count in most_frequent_topics],
    }


@router.get("/users")
def list_users(
    role: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    """Admin-only user list with optional role filter and name/email search."""
    query = db.query(User)
    if role in ("student", "alumni", "admin"):
        query = query.filter(User.role == role)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.filter(func.lower(User.name).like(like) | func.lower(User.email).like(like))
    users = query.order_by(User.id.desc()).all()

    counts = dict(
        db.query(Experience.user_id, func.count(Experience.id))
        .filter(Experience.user_id.isnot(None))
        .group_by(Experience.user_id)
        .all()
    )
    return [{**u.to_dict(), "experience_count": counts.get(u.id, 0)} for u in users]


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(role_required("admin")),
):
    """Admin-only hard delete of a student/alumni account.

    Policy (see user_cleanup.py): experiences are kept and anonymized,
    personal bookmarks/votes are removed. Admin accounts can't be deleted
    from the app (prevents lockout) — demote them in MySQL first.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be deleted from the app")

    anonymized = delete_user_account(db, user)
    return {"message": "User deleted", "experiences_anonymized": anonymized}


# ---------------------------------------------------------------------------
# Suggestions review: pending companies/roles, possible duplicates, approve, merge
# ---------------------------------------------------------------------------

@router.get("/suggestions")
def pending_suggestions(
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    """Companies and roles suggested by users that are waiting for review."""
    companies = []
    for c in db.query(Company).filter_by(status="pending").order_by(Company.id).all():
        similar = db.get(Company, c.similar_to_id) if c.similar_to_id else None
        creator = db.get(User, c.created_by) if c.created_by else None
        companies.append({
            **c.to_dict(),
            "suggested_by": creator.name if creator else None,
            "similar_to": {"id": similar.id, "name": similar.name} if similar else None,
            "experience_count": db.query(Experience).filter_by(company_id=c.id).count(),
        })

    roles = []
    for r in db.query(Role).filter_by(status="pending").order_by(Role.id).all():
        creator = db.get(User, r.created_by) if r.created_by else None
        roles.append({
            **r.to_dict(),
            "company_name": r.company.name,
            "suggested_by": creator.name if creator else None,
        })
    return {"companies": companies, "roles": roles}


@router.get("/duplicates")
def possible_duplicates(
    min_score: int = 80,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    """Pairs of companies whose normalized names look alike, most similar first."""
    companies = db.query(Company).order_by(Company.id).all()
    counts = dict(
        db.query(Experience.company_id, func.count(Experience.id)).group_by(Experience.company_id).all()
    )
    pairs = []
    for i, a in enumerate(companies):
        for b in companies[i + 1:]:
            score = similarity(a.normalized_name, b.normalized_name)
            if score >= min_score:
                pairs.append({
                    "score": score,
                    "a": {"id": a.id, "name": a.name, "status": a.status, "experience_count": counts.get(a.id, 0)},
                    "b": {"id": b.id, "name": b.name, "status": b.status, "experience_count": counts.get(b.id, 0)},
                })
    pairs.sort(key=lambda p: -p["score"])
    return pairs[:50]


@router.post("/companies/{company_id}/approve")
def approve_company(
    company_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.status = "approved"
    db.commit()
    return company.to_dict()


@router.post("/roles/{role_id}/approve")
def approve_role(
    role_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role.status = "approved"
    db.commit()
    return role.to_dict()


@router.post("/companies/merge")
def merge_companies(
    payload: MergeCompaniesIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    """Merge `source` into `target`: everything pointing at source (experiences, roles,
    company bookmarks) is repointed to target, then source is deleted."""
    if payload.source_id == payload.target_id:
        raise HTTPException(status_code=400, detail="Pick two different companies")
    source = db.get(Company, payload.source_id)
    target = db.get(Company, payload.target_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Company not found")

    # Roles: reuse the target's role when the title matches, otherwise move it over.
    target_roles = {r.title.lower(): r for r in target.roles}
    for role in list(source.roles):
        match = target_roles.get(role.title.lower())
        if match:
            db.query(Experience).filter_by(role_id=role.id).update({Experience.role_id: match.id})
            db.delete(role)
        else:
            role.company_id = target.id

    moved = db.query(Experience).filter_by(company_id=source.id).update({Experience.company_id: target.id})

    # Bookmarks on the source company: move them, dropping any a user already has on the target.
    for bm in db.query(Bookmark).filter_by(target_type="company", target_id=source.id).all():
        already = db.query(Bookmark).filter_by(
            user_id=bm.user_id, target_type="company", target_id=target.id
        ).first()
        if already:
            db.delete(bm)
        else:
            bm.target_id = target.id

    db.query(Company).filter(Company.similar_to_id == source.id).update({Company.similar_to_id: None})
    target.status = "approved"  # the admin chose it as the canonical record
    target.similar_to_id = None

    db.flush()
    db.expire(source)  # so deleting it doesn't cascade onto roles we just moved
    db.delete(source)
    db.commit()
    return {"message": "Companies merged", "target": target.to_dict(), "experiences_moved": moved}
