from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark
from app.models.experience import Experience
from app.models.helpful_vote import HelpfulVote
from app.models.report import Report
from app.models.user import User


def delete_user_account(db: Session, user: User) -> int:
    """Shared by the admin delete and the "delete my account" endpoints.

    Experiences are community content: kept, author set to NULL (shown as
    "Anonymous alumnus"). Reports the user filed are kept for moderation.
    Bookmarks and helpful votes are personal, so they are deleted.
    Returns how many experiences were anonymized.
    """
    anonymized = db.query(Experience).filter_by(user_id=user.id).update({Experience.user_id: None})
    db.query(Report).filter_by(user_id=user.id).update({Report.user_id: None})
    db.query(Bookmark).filter_by(user_id=user.id).delete()
    db.query(HelpfulVote).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()
    return anonymized
