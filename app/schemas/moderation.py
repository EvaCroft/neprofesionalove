from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RoleUpdate(BaseModel):
    role: str  # "user" | "creator" | "moderator" | "admin"


class ModeratorAssign(BaseModel):
    room_id: int
    user_id: int


class ReportCreate(BaseModel):
    target_type: str  # "room_message" | "user"
    target_id: int
    room_id: Optional[int] = None
    reason: str


class ReportOut(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    room_id: Optional[int] = None
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class LogOut(BaseModel):
    id: int
    log_type: str
    timestamp: datetime
    actor_user_id: Optional[int] = None
    action: str
    target: Optional[str] = None
    ip_address: Optional[str] = None
    meta: Optional[str] = None

    class Config:
        from_attributes = True
