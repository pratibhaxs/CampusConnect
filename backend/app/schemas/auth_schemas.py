from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Literal["student", "alumni"]  # no public admin signup — see README
    college_id: int
    branch: Optional[str] = Field(default=None, max_length=100)
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2100)


class DeleteAccountIn(BaseModel):
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str
