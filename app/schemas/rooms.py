from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RoomOut(BaseModel):
    id: int
    name: str
    type: str
    owner_id: int
    created_at: datetime
    member_count: int = 0
    entry_fee: str = "0.00"

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str
    type: str = "public"  # "public" | "private"
    entry_fee: str = "0"


class RoomMessageCreate(BaseModel):
    text: str


class RoomMessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    text: Optional[str] = None
    media_id: Optional[int] = None
    sent_at: datetime

    class Config:
        from_attributes = True
