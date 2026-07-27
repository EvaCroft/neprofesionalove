from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    starts_at: datetime
    location: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    location: Optional[str] = None


class EventOut(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    starts_at: datetime
    location: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: datetime
    going_count: int
    interested_count: int
    my_status: Optional[str] = None  # "going" | "interested" | "went" | None

    class Config:
        from_attributes = True


class ParticipationIn(BaseModel):
    status: str  # "going" | "interested" | "went"


class ParticipationOut(BaseModel):
    event_id: int
    user_id: int
    status: str
    created_at: datetime
