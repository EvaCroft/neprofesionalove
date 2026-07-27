from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageCreate(BaseModel):
    to_user_id: int
    text: str


class MessageOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    text: Optional[str] = None
    media_id: Optional[int] = None
    sent_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    other_user_id: int
    last_message: str
    last_sent_at: datetime
    unread_count: int
