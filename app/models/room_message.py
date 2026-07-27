"""Model RoomMessage - zprávy na chat-wall místnosti."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text

from app.db import Base


class RoomMessage(Base):
    __tablename__ = "room_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=True)  # nullable od v20: čistě mediální zpráva nemusí mít text
    media_id = Column(Integer, ForeignKey("media_assets.id"), nullable=True, index=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
