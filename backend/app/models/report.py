from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

VALID_REASONS = ("fake", "inappropriate", "spam", "incorrect")
VALID_STATUSES = ("open", "reviewed")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    experience_id = Column(Integer, ForeignKey("experiences.id"), nullable=False)
    reason = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    experience = relationship("Experience", back_populates="reports")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reporter_name": self.user.name if self.user else "Deleted user",
            "experience_id": self.experience_id,
            "experience_title": (
                f"{self.experience.company.name} — {self.experience.role.title}"
                if self.experience and self.experience.company and self.experience.role else None
            ),
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
