from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostCreate(BaseModel):
    text: Optional[str] = None
    media_id: Optional[int] = None
    target_user_id: Optional[int] = None  # None = na vlastní zeď
    visibility: str = "public"  # "public" | "friends" | "private"


class PostUpdate(BaseModel):
    text: Optional[str] = None
    visibility: Optional[str] = None


class PostOut(BaseModel):
    id: int
    author_id: int
    target_user_id: int
    text: Optional[str] = None
    media_id: Optional[int] = None
    origin: str
    source_action: Optional[str] = None
    visibility: str
    created_at: datetime

    class Config:
        from_attributes = True
