from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, validates

from app.database import Base
from app.matching import normalize_name


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)

    # Duplicate prevention: normalize_name(name), unique so "TCS Ltd" and "tcs" can't coexist.
    normalized_name = Column(String(200), nullable=False, unique=True)
    # "approved" = public; "pending" = user-suggested, visible only to its creator and admins.
    status = Column(String(20), nullable=False, default="approved")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Closest existing company found when this was suggested — helps the admin merge.
    similar_to_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)

    roles = relationship("Role", back_populates="company", cascade="all, delete-orphan")

    @validates("name")
    def _sync_normalized_name(self, _key, value):
        # Keeps normalized_name in step with name everywhere (API, seeds, tests).
        self.normalized_name = normalize_name(value)
        return value

    def to_dict(self, include_roles=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "logo_url": self.logo_url,
            "status": self.status,
        }
        if include_roles:
            data["roles"] = [r.to_dict() for r in self.roles]
        return data
