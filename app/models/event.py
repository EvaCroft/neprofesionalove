"""
Model Event + EventParticipation - modul Události (dokončení profilu, část 4/4).

Účast má 3 stavy: GOING (jde), INTERESTED (zajímá se), WENT (byla) - jeden
řádek na dvojici (event_id, user_id), při změně stavu se přepisuje (ne
historie víc řádků na uživatele u jedné události).

`cover_url` se nastavuje přes modul Média (`MediaSource.EVENT_COVER`, viz
`app/routers/media.py`), stejný vzor jako `Profile.avatar_url`/`cover_url` -
ne přímé textové pole v `EventCreate`/`EventUpdate`.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, UniqueConstraint

from app.db import Base


class ParticipationStatus(str, enum.Enum):
    GOING = "going"
    INTERESTED = "interested"
    WENT = "went"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False, index=True)
    location = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EventParticipation(Base):
    __tablename__ = "event_participations"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_participation"),)

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(ParticipationStatus), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
