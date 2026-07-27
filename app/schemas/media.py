from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MediaAssetOut(BaseModel):
    id: int
    owner_id: int
    media_type: str
    source: str
    original_filename: str
    mime_type: str
    size_bytes: int
    duration_seconds: Optional[int] = None
    room_id: Optional[int] = None
    to_user_id: Optional[int] = None
    created_at: datetime
    url: str  # absolutní/relativní URL pro <img>/<video>/<audio> src
    direction: Optional[str] = None  # "uploaded" | "sent" | "received" - dopočteno vůči current_user

    class Config:
        from_attributes = True


class MediaTypeCount(BaseModel):
    media_type: str
    count: int


class MediaStatsOut(BaseModel):
    total: int
    by_type: List[MediaTypeCount]
