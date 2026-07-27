"""
Model Post - příspěvky na zeď (v20+, "Systém příspěvků").

Post může vzniknout dvěma způsoby:
  - USER_POST        = uživatel jej napsal ručně (přes POST /posts)
  - SYSTEM_GENERATED = vznikl automaticky jako propis jiné akce (nahrání
    média na zeď, založení eventu, ...) - viz app/services/post_service.py
    funkce create_post_from_action().

`target_user_id` = na čí zeď post patří (u ručního postu na vlastní zeď je
stejné jako author_id; u postu napsaného "na zeď kamaráda" se liší).

`visibility` řídí, kdo post vidí - stejná škála jako u profilu
(public/friends/private). Poznámka: systém přátel zatím v projektu není
implementován (mimo MVP scope), takže "friends" se prozatím chová jako
"private" (viditelné jen autorovi a majiteli zdi) - viz post_service.py.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text

from app.db import Base


class PostOrigin(str, enum.Enum):
    USER_POST = "user_post"
    SYSTEM_GENERATED = "system_generated"


class PostVisibility(str, enum.Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    text = Column(Text, nullable=True)
    media_id = Column(Integer, ForeignKey("media_assets.id"), nullable=True)

    origin = Column(Enum(PostOrigin), nullable=False, default=PostOrigin.USER_POST)
    source_action = Column(String, nullable=True)  # např. "media_upload", "event_created" - jen u SYSTEM_GENERATED

    visibility = Column(Enum(PostVisibility), nullable=False, default=PostVisibility.PUBLIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
