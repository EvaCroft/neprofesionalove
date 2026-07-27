"""
Model Room + RoomMembership.

Vytváření místností (endpoint) je až v v5 (jen Creator+role) - v4 obsahuje
jen datový model a čtení/join/leave/messaging nad existujícími místnostmi.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Numeric

from app.db import Base


class RoomType(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(Enum(RoomType), nullable=False, default=RoomType.PUBLIC)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    entry_fee = Column(Numeric(precision=18, scale=2), nullable=False, default=0)  # 0 = zdarma


class RoomMembership(Base):
    __tablename__ = "room_memberships"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    muted = Column(Boolean, nullable=False, default=False)
    banned = Column(Boolean, nullable=False, default=False)
