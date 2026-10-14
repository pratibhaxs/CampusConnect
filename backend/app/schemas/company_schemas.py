from typing import Optional
from pydantic import BaseModel, Field


class CompanyIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class CompanyUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class RoleIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)


class SubmitCompanyIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    confirm_new: bool = False  # True = "No, it's a different company — create it anyway"


class SubmitRoleIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    confirm_new: bool = False


class MergeCompaniesIn(BaseModel):
    source_id: int  # deleted after merge
    target_id: int  # kept
