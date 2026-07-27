"""
Model MediaAsset - Galerie médií.

Sdružuje veškerá média (foto/video/audio/reel) bez ohledu na to, kudy do
systému vstoupila:
  - WALL           = nahráno na zeď profilu
  - DIRECT_UPLOAD  = nahráno přímo do galerie (bez vazby na příspěvek)
  - MESSENGER      = odesláno/přijato jako příloha přímé zprávy (viz DirectMessage.media_id)
  - ROOM           = sdíleno v chatu místnosti (viz RoomMessage.media_id)
  - PROFILE_AVATAR = nahráno jako profilovka (viz Profile.avatar_url, v21)
  - PROFILE_COVER  = nahráno jako úvodní/cover obrázek (viz Profile.cover_url, v21)
  - EVENT_COVER    = nahráno jako cover obrázek události (viz Event.cover_url, v20 část 4/4)

`owner_id` je vždy uživatel, který soubor nahrál/odeslal (autor obsahu).
Pro MESSENGER položky navíc `to_user_id` říká, komu byla zpráva adresována -
umožňuje to rozlišit směr (odesláno/přijato) bez nutnosti joinovat
direct_messages při každém dotazu do galerie.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum

from app.db import Base


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    REEL = "reel"


class MediaSource(str, enum.Enum):
    WALL = "wall"
    DIRECT_UPLOAD = "direct_upload"
    MESSENGER = "messenger"
    ROOM = "room"
    PROFILE_AVATAR = "profile_avatar"
    PROFILE_COVER = "profile_cover"
    EVENT_COVER = "event_cover"


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    media_type = Column(Enum(MediaType), nullable=False, index=True)
    source = Column(Enum(MediaSource), nullable=False, index=True)

    file_path = Column(String, nullable=False)       # relativní cesta na disku
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=True)  # jen video/audio/reel

    # Volitelné vazby podle zdroje (přesně jedna dává smysl podle `source`):
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
