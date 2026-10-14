from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

ANONYMOUS_AUTHOR = "Anonymous alumnus"
VALID_STATUSES = ("pending", "approved", "rejected")


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True)

    # NULL = author account was deleted; the experience stays as community content.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)

    branch = Column(String(100), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    placement_year = Column(Integer, nullable=False)
    package = Column(String(50), nullable=True)

    overall_experience = Column(Text, nullable=True)
    preparation_tips = Column(Text, nullable=True)
    additional_advice = Column(Text, nullable=True)
    selected = Column(Boolean, nullable=False, default=False)

    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    company = relationship("Company")
    role = relationship("Role")
    college = relationship("College")
    rounds = relationship(
        "RecruitmentRound", back_populates="experience",
        cascade="all, delete-orphan", order_by="RecruitmentRound.round_number",
    )
    helpful_votes = relationship("HelpfulVote", back_populates="experience", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="experience", cascade="all, delete-orphan")

    def to_dict(self, include_rounds=False, current_user_id=None):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else ANONYMOUS_AUTHOR,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "role_id": self.role_id,
            "role_title": self.role.title if self.role else None,
            "college_id": self.college_id,
            "college_name": self.college.name if self.college else None,
            "branch": self.branch,
            "graduation_year": self.graduation_year,
            "placement_year": self.placement_year,
            "package": self.package,
            "overall_experience": self.overall_experience,
            "preparation_tips": self.preparation_tips,
            "additional_advice": self.additional_advice,
            "selected": self.selected,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "helpful_count": len(self.helpful_votes),
        }
        if current_user_id is not None:
            data["user_has_voted_helpful"] = any(v.user_id == current_user_id for v in self.helpful_votes)
        if include_rounds:
            data["rounds"] = [r.to_dict(include_questions=True) for r in self.rounds]
        return data
