"""
Model FriendRequest - vzájemné přátelství (v24, blok "Vztahy").

Jedna tabulka pokrývá celý životní cyklus žádosti o přátelství, ne dvě
oddělené (žádost vs. přátelství) - řádek se `status='pending'` je otevřená
žádost, `status='accepted'` je aktivní přátelství. Odmítnutí/zrušení/
zrušení přátelství (unfriend) řádek rovnou maže (žádná historie odmítnutých
žádostí) - umožní to poslat žádost znovu později, jednodušší než stavový
"declined" navždy blokující nové žádosti.

Směr (`from_user_id`/`to_user_id`) se drží i po přijetí (i když je vztah
pak už symetrický) - dává smysl vědět, kdo žádost původně poslal.

Aplikačně (ne DB constraintem, SQLite to neumí čistě přes UniqueConstraint
na neuspořádanou dvojici) hlídáno v routeru: mezi dvěma uživateli smí
existovat max. jeden řádek (v libovolném směru) najednou.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum

from app.db import Base


class FriendRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(FriendRequestStatus), nullable=False, default=FriendRequestStatus.PENDING, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
