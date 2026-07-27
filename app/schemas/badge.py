# --- v25: Odznaky ---

from typing import Optional, List

from pydantic import BaseModel


class BadgeOut(BaseModel):
    key: str
    emoji: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class BadgeCreate(BaseModel):
    key: str
    emoji: str
    name: str


class BadgeUpdate(BaseModel):
    emoji: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class UserBadgesUpdate(BaseModel):
    badge_keys: List[str]
