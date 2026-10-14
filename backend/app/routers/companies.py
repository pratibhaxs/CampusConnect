from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.role import Role
from app.models.experience import Experience
from app.models.round import RecruitmentRound
from app.models.question import Question
from app.models.user import User
from app.schemas.company_schemas import CompanyIn, CompanyUpdateIn, RoleIn, SubmitCompanyIn, SubmitRoleIn
from app.matching import DEFAULT_THRESHOLD, FLAG_THRESHOLD, find_matches, normalize_name
from app.security import get_current_user_optional, role_required

router = APIRouter(prefix="/companies", tags=["companies"])

DIFFICULTY_SCORE = {"easy": 1, "medium": 2, "hard": 3}
SCORE_TO_DIFFICULTY = {1: "easy", 2: "medium", 3: "hard"}


def _can_see(item, user: Optional[User]) -> bool:
    """Approved items are public; pending ones only to their creator and admins."""
    if item.status == "approved":
        return True
    return user is not None and (user.role == "admin" or item.created_by == user.id)


def _visible_companies_query(db: Session, user: Optional[User]):
    query = db.query(Company)
    if user is None:
        return query.filter(Company.status == "approved")
    if user.role == "admin":
        return query
    return query.filter((Company.status == "approved") | (Company.created_by == user.id))


@router.get("")
def list_companies(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Public. Supports ?q=<search text> for name search (used by the student search bar).
    Pending (user-suggested) companies are only listed for their creator and admins."""
    query = _visible_companies_query(db, current_user)
    if q and q.strip():
        query = query.filter(Company.name.ilike(f"%{q.strip()}%"))

    companies = query.order_by(Company.name).all()
    result = []
    for c in companies:
        data = c.to_dict()
        data["experience_count"] = db.query(Experience).filter_by(company_id=c.id, status="approved").count()
        result.append(data)
    return result


@router.get("/suggest")
def suggest_companies(
    name: str,
    db: Session = Depends(get_db),
    _user: User = Depends(role_required("student", "alumni", "admin")),
):
    """Fuzzy 'did you mean' lookup for the typed company name."""
    matches = find_matches(name, db.query(Company).all(), min_score=DEFAULT_THRESHOLD)
    return {"matches": matches}


@router.post("/submit")
def submit_company(
    payload: SubmitCompanyIn,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni", "admin")),
):
    """Alumni suggest a company that isn't listed.

    - Same normalized name already exists  -> return that company (no duplicate).
    - Similar names exist and confirm_new is false -> ask the user to confirm.
    - Otherwise create it as `pending` (admin approves/merges later).
    """
    normalized = normalize_name(payload.name)
    existing = db.query(Company).filter_by(normalized_name=normalized).first()
    if existing:
        if not _can_see(existing, current_user):
            raise HTTPException(status_code=409, detail="This company is awaiting admin review")
        return {"created": False, "needs_confirmation": False, "matches": [], "company": existing.to_dict()}

    all_companies = db.query(Company).all()
    close = find_matches(payload.name, all_companies, min_score=DEFAULT_THRESHOLD)
    if close and not payload.confirm_new:
        return {"created": False, "needs_confirmation": True, "matches": close, "company": None}

    related = find_matches(payload.name, all_companies, min_score=FLAG_THRESHOLD, limit=1)
    company = Company(
        name=payload.name.strip(),
        status="approved" if current_user.role == "admin" else "pending",
        created_by=current_user.id,
        similar_to_id=related[0]["id"] if related else None,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    response.status_code = 201
    return {"created": True, "needs_confirmation": False, "matches": close, "company": company.to_dict()}


@router.get("/{company_id}")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Public. Full detail including roles, for the company page."""
    company = db.get(Company, company_id)
    if not company or not _can_see(company, current_user):
        raise HTTPException(status_code=404, detail="Company not found")
    data = company.to_dict()
    data["roles"] = [r.to_dict() for r in company.roles if _can_see(r, current_user)]
    data["experience_count"] = db.query(Experience).filter_by(company_id=company.id, status="approved").count()
    return data


@router.get("/{company_id}/stats")
def get_company_stats(company_id: int, db: Session = Depends(get_db)):
    """
    Public. The "Placement Intelligence Dashboard" for one company — computed
    live from approved experiences with plain SQL aggregation (no ML).
    """
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    approved_experiences = db.query(Experience).filter_by(company_id=company_id, status="approved").all()
    total = len(approved_experiences)

    if total == 0:
        return {
            "total_experiences": 0,
            "average_rounds": 0,
            "most_common_first_round": None,
            "topic_percentages": [],
            "average_difficulty": None,
        }

    exp_ids = [e.id for e in approved_experiences]

    round_counts = (
        db.query(RecruitmentRound.experience_id, func.count(RecruitmentRound.id))
        .filter(RecruitmentRound.experience_id.in_(exp_ids))
        .group_by(RecruitmentRound.experience_id)
        .all()
    )
    total_rounds = sum(count for _, count in round_counts)
    average_rounds = round(total_rounds / total, 1) if total else 0

    first_rounds = (
        db.query(RecruitmentRound.round_type)
        .filter(RecruitmentRound.experience_id.in_(exp_ids), RecruitmentRound.round_number == 1)
        .all()
    )
    most_common_first_round = None
    if first_rounds:
        counter = Counter(r[0] for r in first_rounds)
        most_common_first_round = counter.most_common(1)[0][0]

    topic_rows = (
        db.query(Experience.id, func.lower(Question.topic))
        .join(RecruitmentRound, RecruitmentRound.experience_id == Experience.id)
        .join(Question, Question.round_id == RecruitmentRound.id)
        .filter(Experience.id.in_(exp_ids), Question.topic.isnot(None), Question.topic != "")
        .all()
    )
    topic_to_exp_ids: dict = {}
    for exp_id, lower_topic in topic_rows:
        topic_to_exp_ids.setdefault(lower_topic, set()).add(exp_id)

    original_rows = (
        db.query(func.lower(Question.topic), Question.topic)
        .join(RecruitmentRound, Question.round_id == RecruitmentRound.id)
        .filter(RecruitmentRound.experience_id.in_(exp_ids), Question.topic.isnot(None), Question.topic != "")
        .all()
    )
    topic_display_names: dict = {}
    for lower_topic, original in original_rows:
        topic_display_names.setdefault(lower_topic, original)

    topic_percentages = sorted(
        [
            {
                "topic": topic_display_names.get(lower_topic, lower_topic),
                "percentage": round(len(exp_id_set) / total * 100),
            }
            for lower_topic, exp_id_set in topic_to_exp_ids.items()
        ],
        key=lambda t: t["percentage"],
        reverse=True,
    )[:10]

    difficulty_rows = (
        db.query(RecruitmentRound.difficulty)
        .filter(RecruitmentRound.experience_id.in_(exp_ids), RecruitmentRound.difficulty.isnot(None))
        .all()
    )
    scores = [DIFFICULTY_SCORE[d[0]] for d in difficulty_rows if d[0] in DIFFICULTY_SCORE]
    average_difficulty = None
    if scores:
        avg_score = round(sum(scores) / len(scores))
        average_difficulty = SCORE_TO_DIFFICULTY.get(avg_score, "medium")

    return {
        "total_experiences": total,
        "average_rounds": average_rounds,
        "most_common_first_round": most_common_first_round,
        "topic_percentages": topic_percentages,
        "average_difficulty": average_difficulty,
    }


@router.get("/{company_id}/recommendation")
def get_company_recommendation(company_id: int, role_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Public. "Recommended Preparation" for a company (optionally scoped to a
    specific ?role_id=). Reuses the same topic-frequency data as /stats.
    """
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    exp_query = db.query(Experience).filter_by(company_id=company_id, status="approved")
    if role_id:
        exp_query = exp_query.filter_by(role_id=role_id)
    approved_experiences = exp_query.all()
    total = len(approved_experiences)

    if total == 0:
        return {"recommended_topics": [], "frequent_questions": [], "based_on": 0}

    exp_ids = [e.id for e in approved_experiences]

    topic_rows = (
        db.query(Experience.id, func.lower(Question.topic), Question.topic)
        .join(RecruitmentRound, RecruitmentRound.experience_id == Experience.id)
        .join(Question, Question.round_id == RecruitmentRound.id)
        .filter(Experience.id.in_(exp_ids), Question.topic.isnot(None), Question.topic != "")
        .all()
    )
    topic_to_exp_ids: dict = {}
    topic_display_names: dict = {}
    for exp_id, lower_topic, original_topic in topic_rows:
        topic_to_exp_ids.setdefault(lower_topic, set()).add(exp_id)
        topic_display_names.setdefault(lower_topic, original_topic)

    def percentage_to_stars(pct: int) -> int:
        return max(1, min(5, -(-pct // 20) or 1))  # ceil division, floor at 1

    recommended_topics = sorted(
        [
            {
                "topic": topic_display_names[lower_topic],
                "percentage": round(len(ids) / total * 100),
                "stars": percentage_to_stars(round(len(ids) / total * 100)),
            }
            for lower_topic, ids in topic_to_exp_ids.items()
        ],
        key=lambda t: t["percentage"],
        reverse=True,
    )[:8]

    question_rows = (
        db.query(Question.question_text, Question.category, Question.topic)
        .join(RecruitmentRound, Question.round_id == RecruitmentRound.id)
        .filter(RecruitmentRound.experience_id.in_(exp_ids))
        .all()
    )
    question_counts: dict = {}
    for text, category, topic in question_rows:
        key = text.strip().lower()
        if key not in question_counts:
            question_counts[key] = {"question_text": text, "category": category, "topic": topic, "count": 0}
        question_counts[key]["count"] += 1

    frequent_questions = sorted(question_counts.values(), key=lambda q: q["count"], reverse=True)[:8]

    return {
        "recommended_topics": recommended_topics,
        "frequent_questions": frequent_questions,
        "based_on": total,
    }


@router.post("", status_code=201)
def create_company(
    payload: CompanyIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    if db.query(Company).filter_by(normalized_name=normalize_name(payload.name)).first():
        raise HTTPException(status_code=409, detail="Company already exists")

    company = Company(name=payload.name, description=payload.description, logo_url=payload.logo_url)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company.to_dict()


@router.put("/{company_id}")
def update_company(
    company_id: int,
    payload: CompanyUpdateIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        existing = db.query(Company).filter_by(normalized_name=normalize_name(data["name"])).first()
        if existing and existing.id != company_id:
            raise HTTPException(status_code=409, detail="Another company already has that name")
        company.name = data["name"]
    if "description" in data:
        company.description = data["description"]
    if "logo_url" in data:
        company.logo_url = data["logo_url"]

    db.commit()
    db.refresh(company)
    return company.to_dict()


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)  # roles cascade-delete
    db.commit()
    return {"message": "Company deleted"}


@router.post("/{company_id}/roles", status_code=201)
def add_role(
    company_id: int,
    payload: RoleIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if db.query(Role).filter_by(company_id=company_id, title=payload.title).first():
        raise HTTPException(status_code=409, detail="This role already exists for this company")

    role = Role(company_id=company_id, title=payload.title)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role.to_dict()


@router.post("/{company_id}/roles/submit")
def submit_role(
    company_id: int,
    payload: SubmitRoleIn,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni", "admin")),
):
    """Alumni suggest a missing role for a company. Same flow as companies:
    exact (case/space-insensitive) match reuses the role, similar titles ask for
    confirmation, otherwise a `pending` role is created for admin review."""
    company = db.get(Company, company_id)
    if not company or not _can_see(company, current_user):
        raise HTTPException(status_code=404, detail="Company not found")

    title = " ".join(payload.title.split())
    roles = [r for r in company.roles if _can_see(r, current_user)]
    for r in roles:
        if r.title.lower() == title.lower():
            return {"created": False, "needs_confirmation": False, "matches": [], "role": r.to_dict()}

    class _R:  # adapt Role to the matcher's (id, name, normalized_name) shape
        def __init__(self, r): self.id, self.name, self.normalized_name = r.id, r.title, normalize_name(r.title)

    close = find_matches(title, [_R(r) for r in roles], min_score=DEFAULT_THRESHOLD)
    if close and not payload.confirm_new:
        return {"created": False, "needs_confirmation": True, "matches": close, "role": None}

    role = Role(
        company_id=company_id, title=title, created_by=current_user.id,
        status="approved" if current_user.role == "admin" else "pending",
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    response.status_code = 201
    return {"created": True, "needs_confirmation": False, "matches": close, "role": role.to_dict()}


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"message": "Role deleted"}
