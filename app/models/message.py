"""Model DirectMessage - přímé zprávy mezi dvěma uživateli (messenger)."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from app.db import Base


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=True)  # nullable od v20: čistě mediální zpráva nemusí mít text
    media_id = Column(Integer, ForeignKey("media_assets.id"), nullable=True, index=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    read_at = Column(DateTime, nullable=True)
