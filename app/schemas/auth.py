from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import RoleEnum


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
