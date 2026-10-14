from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.experience import Experience
from app.models.round import RecruitmentRound
from app.models.question import Question
from app.models.company import Company
from app.models.role import Role
from app.models.college import College
from app.models.user import User
from app.models.helpful_vote import HelpfulVote
from app.schemas.experience_schemas import ExperienceIn, StatusUpdateIn
from app.security import get_current_user, get_current_user_optional, role_required

router = APIRouter(prefix="/experiences", tags=["experiences"])


def _build_rounds(db: Session, experience: Experience, rounds_data) -> None:
    """Used by both create and update — replaces all rounds/questions for an
    experience from the nested payload, matching how the multi-step form
    always submits the whole set."""
    for round_data in rounds_data:
        round_obj = RecruitmentRound(
            experience_id=experience.id,
            round_number=round_data.round_number,
            round_type=round_data.round_type,
            description=round_data.description,
            difficulty=round_data.difficulty,
        )
        db.add(round_obj)
        db.flush()  # so round_obj.id is available for questions

        for q in round_data.questions:
            db.add(Question(
                round_id=round_obj.id,
                question_text=q.question_text,
                category=q.category,
                topic=q.topic,
                difficulty=q.difficulty,
            ))


def _validate_references(db: Session, payload, user: User):
    """Company/role/college must exist, the role must belong to the company, and a
    still-pending (user-suggested) company or role may only be used by its creator."""
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=400, detail="Invalid company_id")
    role = db.get(Role, payload.role_id)
    if not role or role.company_id != payload.company_id:
        raise HTTPException(status_code=400, detail="Invalid role_id for this company")
    for item, label in ((company, "company"), (role, "role")):
        if item.status != "approved" and item.created_by != user.id:
            raise HTTPException(status_code=400, detail=f"Invalid {label}")
    if not db.get(College, payload.college_id):
        raise HTTPException(status_code=400, detail="Invalid college_id")


@router.post("", status_code=201)
def create_experience(
    payload: ExperienceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni")),
):
    _validate_references(db, payload, current_user)

    experience = Experience(
        user_id=current_user.id,
        company_id=payload.company_id,
        role_id=payload.role_id,
        college_id=payload.college_id,
        branch=payload.branch,
        graduation_year=payload.graduation_year,
        placement_year=payload.placement_year,
        package=payload.package,
        overall_experience=payload.overall_experience,
        preparation_tips=payload.preparation_tips,
        additional_advice=payload.additional_advice,
        selected=payload.selected,
        status="pending",
    )
    db.add(experience)
    db.flush()

    _build_rounds(db, experience, payload.rounds)

    db.commit()
    db.refresh(experience)
    return experience.to_dict(include_rounds=True)


@router.get("/mine")
def my_experiences(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni")),
):
    experiences = (
        db.query(Experience).filter_by(user_id=current_user.id)
        .order_by(Experience.created_at.desc()).all()
    )
    return [e.to_dict(current_user_id=current_user.id) for e in experiences]


@router.get("")
def list_experiences(
    company_id: Optional[int] = None,
    college_id: Optional[int] = None,
    role_id: Optional[int] = None,
    year: Optional[int] = None,
    branch: Optional[str] = None,
    difficulty: Optional[str] = None,
    round_type: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Publicly viewable, but only 'approved' experiences show up unless the
    requester is the owner or an admin. `status` filter is admin-only (powers
    the approval queue) and is silently ignored for everyone else.
    """
    query = db.query(Experience)

    if company_id:
        query = query.filter(Experience.company_id == company_id)
    if college_id:
        query = query.filter(Experience.college_id == college_id)
    if role_id:
        query = query.filter(Experience.role_id == role_id)
    if year:
        query = query.filter(Experience.placement_year == year)
    if branch and branch.strip():
        query = query.filter(Experience.branch.ilike(f"%{branch.strip()}%"))

    needs_round_join = bool(difficulty or round_type or topic)
    if needs_round_join:
        query = query.join(RecruitmentRound, RecruitmentRound.experience_id == Experience.id)
        if difficulty:
            query = query.filter(RecruitmentRound.difficulty == difficulty)
        if round_type and round_type.strip():
            query = query.filter(RecruitmentRound.round_type.ilike(f"%{round_type.strip()}%"))
        if topic and topic.strip():
            query = query.join(Question, Question.round_id == RecruitmentRound.id) \
                          .filter(Question.topic.ilike(f"%{topic.strip()}%"))

    role = current_user.role if current_user else None

    if role == "admin":
        if status and status.strip():
            query = query.filter(Experience.status == status.strip())
    elif current_user:
        query = query.filter(
            (Experience.status == "approved") | (Experience.user_id == current_user.id)
        )
    else:
        query = query.filter(Experience.status == "approved")

    experiences = query.order_by(Experience.created_at.desc()).all()

    seen = set()
    unique_experiences = []
    for e in experiences:
        if e.id not in seen:
            seen.add(e.id)
            unique_experiences.append(e)

    current_user_id = current_user.id if current_user else None
    return [e.to_dict(current_user_id=current_user_id) for e in unique_experiences]


@router.get("/{experience_id}")
def get_experience(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    experience = db.get(Experience, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")

    is_owner = current_user is not None and current_user.id == experience.user_id
    role = current_user.role if current_user else None
    if experience.status != "approved" and not is_owner and role != "admin":
        raise HTTPException(status_code=403, detail="This experience is not available")

    current_user_id = current_user.id if current_user else None
    return experience.to_dict(include_rounds=True, current_user_id=current_user_id)


@router.put("/{experience_id}")
def update_experience(
    experience_id: int,
    payload: ExperienceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni")),
):
    experience = db.get(Experience, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    if experience.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own experiences")

    _validate_references(db, payload, current_user)
    experience.company_id = payload.company_id
    experience.role_id = payload.role_id
    experience.college_id = payload.college_id
    experience.branch = payload.branch
    experience.graduation_year = payload.graduation_year
    experience.placement_year = payload.placement_year
    experience.package = payload.package
    experience.overall_experience = payload.overall_experience
    experience.preparation_tips = payload.preparation_tips
    experience.additional_advice = payload.additional_advice
    experience.selected = payload.selected
    # Editing sends it back for re-approval — keeps moderation meaningful.
    experience.status = "pending"

    for r in list(experience.rounds):
        db.delete(r)
    db.flush()
    _build_rounds(db, experience, payload.rounds)

    db.commit()
    db.refresh(experience)
    return experience.to_dict(include_rounds=True)


@router.delete("/{experience_id}")
def delete_experience(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("alumni")),
):
    experience = db.get(Experience, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    if experience.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own experiences")

    db.delete(experience)
    db.commit()
    return {"message": "Experience deleted"}


@router.put("/{experience_id}/status")
def update_status(
    experience_id: int,
    payload: StatusUpdateIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(role_required("admin")),
):
    experience = db.get(Experience, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")

    if payload.status == "approved" and (
        experience.company.status != "approved" or experience.role.status != "approved"
    ):
        raise HTTPException(
            status_code=400,
            detail="Approve or merge the suggested company/role first (Admin > Suggestions).",
        )

    experience.status = payload.status
    db.commit()
    db.refresh(experience)
    return experience.to_dict()


@router.post("/{experience_id}/helpful")
def toggle_helpful(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("student")),
):
    """Toggles the current student's helpful vote — one vote per user, plain like/unlike."""
    experience = db.get(Experience, experience_id)
    if not experience or experience.status != "approved":
        raise HTTPException(status_code=404, detail="Experience not found")

    existing = db.query(HelpfulVote).filter_by(user_id=current_user.id, experience_id=experience_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        voted = False
    else:
        db.add(HelpfulVote(user_id=current_user.id, experience_id=experience_id))
        db.commit()
        voted = True

    db.refresh(experience)
    return {"helpful_count": len(experience.helpful_votes), "user_has_voted_helpful": voted}
