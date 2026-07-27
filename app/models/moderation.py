"""
Modely pro moderaci: přiřazení moderátorů k místnostem + fronta reportů.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text

from app.db import Base


class RoomModerator(Base):
    """Přiřazení moderátora ke konkrétní místnosti (zadává Admin)."""
    __tablename__ = "room_moderators"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    moderator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ReportTargetType(str, enum.Enum):
    ROOM_MESSAGE = "room_message"
    USER = "user"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum(ReportTargetType), nullable=False)
    target_id = Column(Integer, nullable=False)  # message_id nebo user_id dle target_type
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)  # pro room_message reporty
    reason = Column(Text, nullable=False)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.OPEN)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
