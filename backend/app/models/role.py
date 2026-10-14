from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(150), nullable=False)
    status = Column(String(20), nullable=False, default="approved")  # "pending" = user-suggested
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (UniqueConstraint("company_id", "title", name="uq_company_role_title"),)

    company = relationship("Company", back_populates="roles")

    def to_dict(self):
        return {"id": self.id, "company_id": self.company_id, "title": self.title, "status": self.status}
