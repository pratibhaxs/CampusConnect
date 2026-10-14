from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bookmark import Bookmark
from app.models.experience import Experience
from app.models.question import Question
from app.models.company import Company
from app.models.user import User
from app.schemas.bookmark_schemas import BookmarkIn
from app.security import role_required

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _target_exists(db: Session, target_type: str, target_id: int) -> bool:
    if target_type == "experience":
        exp = db.get(Experience, target_id)
        # students only ever see approved experiences, so only those are bookmarkable
        return exp is not None and exp.status == "approved"
    if target_type == "question":
        return db.get(Question, target_id) is not None
    if target_type == "company":
        company = db.get(Company, target_id)
        return company is not None and company.status == "approved"  # pending suggestions aren't public
    return False


def _resolve_target(db: Session, bookmark: Bookmark) -> dict:
    data = bookmark.to_dict()
    if bookmark.target_type == "experience":
        exp = db.get(Experience, bookmark.target_id)
        data["preview"] = {
            "title": f"{exp.company.name} — {exp.role.title}",
            "subtitle": f"{exp.college.name} · {exp.placement_year}",
        } if exp else None
    elif bookmark.target_type == "question":
        qn = db.get(Question, bookmark.target_id)
        data["preview"] = {
            "title": qn.question_text,
            "subtitle": qn.topic or qn.category or "",
            "experience_id": qn.round.experience_id if qn.round else None,
        } if qn else None
    elif bookmark.target_type == "company":
        c = db.get(Company, bookmark.target_id)
        data["preview"] = {"title": c.name, "subtitle": c.description or ""} if c else None
    return data


@router.get("")
def list_bookmarks(
    target_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("student")),
):
    query = db.query(Bookmark).filter_by(user_id=current_user.id)
    if target_type:
        query = query.filter_by(target_type=target_type)

    bookmarks = query.order_by(Bookmark.created_at.desc()).all()
    return [_resolve_target(db, b) for b in bookmarks]


@router.post("", status_code=201)
def create_bookmark(
    payload: BookmarkIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("student")),
):
    if not _target_exists(db, payload.target_type, payload.target_id):
        raise HTTPException(status_code=404, detail="Target not found or not available to bookmark")

    existing = db.query(Bookmark).filter_by(
        user_id=current_user.id, target_type=payload.target_type, target_id=payload.target_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already bookmarked")

    bookmark = Bookmark(user_id=current_user.id, target_type=payload.target_type, target_id=payload.target_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return _resolve_target(db, bookmark)


@router.delete("/{bookmark_id}")
def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("student")),
):
    bookmark = db.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark removed"}
