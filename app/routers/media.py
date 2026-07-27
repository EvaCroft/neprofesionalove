"""
Router Galerie médií - viz PROJECT.md a frontend/layout-media-galerie.html.

Sdružuje veškerá média (foto/video/audio/reel), která uživatel:
  - nahrál na zeď profilu nebo přímo do galerie (WALL / DIRECT_UPLOAD),
  - odeslal někomu jinému přes messenger nebo do chatu místnosti (MESSENGER / ROOM,
    owner_id == aktuální uživatel),
  - dostal od někoho jiného přes messenger, nebo bylo sdíleno v místnosti,
    jejíž je členem (owner_id != aktuální uživatel).

Přístup ke konkrétnímu médiu (detail i výpis) je vždy omezen jen na tyto tři
případy - `_accessible_media_filter()` je jediné místo, kde se toto pravidlo
definuje, aby se nerozjelo na víc míst.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.media import MediaAsset, MediaSource, MediaType
from app.models.message import DirectMessage
from app.models.event import Event
from app.models.profile import Profile
from app.models.room import Room, RoomMembership
from app.models.room_message import RoomMessage
from app.models.user import RoleEnum, User
from app.permissions import require_role
from app.schemas import MediaAssetOut, MediaStatsOut, MediaTypeCount
from app.services import media_service, post_service

router = APIRouter(prefix="/media", tags=["media"])


def _member_room_ids(db: Session, user_id: int) -> List[int]:
    owned = [r.id for r in db.query(Room.id).filter(Room.owner_id == user_id).all()]
    joined = [
        m.room_id for m in db.query(RoomMembership.room_id)
        .filter(RoomMembership.user_id == user_id, RoomMembership.banned.is_(False))
        .all()
    ]
    return list(set(owned) | set(joined))


def _accessible_media_filter(db: Session, current_user: User):
    """SQLAlchemy podmínka: médium je 'moje', nebo mi bylo poslané přes
    messenger, nebo je sdílené v místnosti, jejíž jsem členem/vlastníkem."""
    room_ids = _member_room_ids(db, current_user.id)
    return or_(
        MediaAsset.owner_id == current_user.id,
        and_(MediaAsset.source == MediaSource.MESSENGER, MediaAsset.to_user_id == current_user.id),
        and_(MediaAsset.source == MediaSource.ROOM, MediaAsset.room_id.in_(room_ids or [-1])),
    )


def _direction_for(asset: MediaAsset, current_user: User) -> str:
    if asset.owner_id == current_user.id:
        if asset.source in (
            MediaSource.WALL, MediaSource.DIRECT_UPLOAD,
            MediaSource.PROFILE_AVATAR, MediaSource.PROFILE_COVER, MediaSource.EVENT_COVER,
        ):
            return "uploaded"
        return "sent"
    return "received"


def _get_or_create_profile(db: Session, user_id: int) -> Profile:
    """Duplikuje minimální logiku z app/routers/profile.py - vědomě, aby se
    nevytvořil kruhový import mezi routery jen kvůli jedné pomocné funkci."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _to_out(asset: MediaAsset, current_user: User) -> MediaAssetOut:
    return MediaAssetOut(
        id=asset.id,
        owner_id=asset.owner_id,
        media_type=asset.media_type.value,
        source=asset.source.value,
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        duration_seconds=asset.duration_seconds,
        room_id=asset.room_id,
        to_user_id=asset.to_user_id,
        created_at=asset.created_at,
        url=media_service.to_url(asset.file_path),
        direction=_direction_for(asset, current_user),
    )


@router.post("/upload", response_model=MediaAssetOut, status_code=status.HTTP_201_CREATED)
def upload_media(
    request: Request,
    file: UploadFile = File(...),
    source: str = Form(...),  # "wall" | "direct_upload" | "messenger" | "room"
    media_type: Optional[str] = Form(None),  # "photo"|"video"|"audio"|"reel" - povinné, pokud mime nestačí (např. reel)
    to_user_id: Optional[int] = Form(None),  # povinné pro source="messenger"
    room_id: Optional[int] = Form(None),  # povinné pro source="room"
    event_id: Optional[int] = Form(None),  # povinné pro source="event_cover"
    caption: Optional[str] = Form(None),  # volitelný text zprávy/postu k médiu
    duration_seconds: Optional[int] = Form(None),
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None

    try:
        source_enum = MediaSource(source)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Neznámý zdroj: {source}")

    if source_enum == MediaSource.MESSENGER and not to_user_id:
        raise HTTPException(status_code=400, detail="source=messenger vyžaduje to_user_id")
    if source_enum == MediaSource.ROOM and not room_id:
        raise HTTPException(status_code=400, detail="source=room vyžaduje room_id")
    if source_enum == MediaSource.EVENT_COVER and not event_id:
        raise HTTPException(status_code=400, detail="source=event_cover vyžaduje event_id")

    recipient = None
    if source_enum == MediaSource.MESSENGER:
        if to_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Nelze poslat médium sám sobě")
        recipient = db.query(User).filter(User.id == to_user_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Příjemce nenalezen")

    room = None
    if source_enum == MediaSource.ROOM:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Místnost nenalezena")
        is_member = room.owner_id == current_user.id or db.query(RoomMembership).filter(
            RoomMembership.room_id == room_id,
            RoomMembership.user_id == current_user.id,
            RoomMembership.banned.is_(False),
        ).first()
        if not is_member:
            raise HTTPException(status_code=403, detail="Nejsi členem této místnosti")

    event = None
    if source_enum == MediaSource.EVENT_COVER:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Událost nenalezena")
        if event.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Jen zakladatel může nastavit cover události")

    resolved_type = media_service.infer_media_type(file.content_type or "", media_type)

    if source_enum in (MediaSource.PROFILE_AVATAR, MediaSource.PROFILE_COVER, MediaSource.EVENT_COVER) and resolved_type != MediaType.PHOTO:
        raise HTTPException(status_code=400, detail="Profilovka, úvodní obrázek a cover události musí být fotka")

    stored_name, size_bytes = media_service.save_upload(file)

    asset = MediaAsset(
        owner_id=current_user.id,
        media_type=resolved_type,
        source=source_enum,
        file_path=stored_name,
        original_filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        duration_seconds=duration_seconds,
        room_id=room_id if source_enum == MediaSource.ROOM else None,
        to_user_id=to_user_id if source_enum == MediaSource.MESSENGER else None,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # U messenger/room zdrojů médium zároveň vytváří samotnou zprávu, na kterou je navázané.
    if source_enum == MediaSource.MESSENGER:
        message = DirectMessage(
            from_user_id=current_user.id,
            to_user_id=to_user_id,
            text=caption,
            media_id=asset.id,
        )
        db.add(message)
        db.commit()
    elif source_enum == MediaSource.ROOM:
        room_message = RoomMessage(
            room_id=room_id,
            user_id=current_user.id,
            text=caption,
            media_id=asset.id,
        )
        db.add(room_message)
        db.commit()
    elif source_enum in (MediaSource.PROFILE_AVATAR, MediaSource.PROFILE_COVER):
        profile = _get_or_create_profile(db, current_user.id)
        url = media_service.to_url(stored_name)
        if source_enum == MediaSource.PROFILE_AVATAR:
            profile.avatar_url = url
        else:
            profile.cover_url = url
        db.commit()
    elif source_enum == MediaSource.EVENT_COVER:
        event.cover_url = media_service.to_url(stored_name)
        db.commit()

    if source_enum == MediaSource.WALL:
        post_service.create_post_from_action(
            db, actor_id=current_user.id, action_key="media_upload",
            text=caption, media_id=asset.id,
        )

    log_event(
        db, LogType.SYSTEM_MEDIA_LOG,
        action="media_uploaded",
        actor_user_id=current_user.id,
        target=str(asset.id),
        ip_address=ip,
        meta={"source": source, "media_type": resolved_type.value, "size_bytes": size_bytes},
    )

    return _to_out(asset, current_user)


@router.get("/stats", response_model=MediaStatsOut)
def media_stats(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    base = db.query(MediaAsset).filter(_accessible_media_filter(db, current_user))
    total = base.count()
    by_type = [
        MediaTypeCount(media_type=t.value, count=base.filter(MediaAsset.media_type == t).count())
        for t in MediaType
    ]
    return MediaStatsOut(total=total, by_type=by_type)


@router.get("", response_model=List[MediaAssetOut])
def list_media(
    media_type: Optional[str] = None,
    source: Optional[str] = None,
    direction: Optional[str] = None,  # "uploaded" | "sent" | "received" | None(=vše)
    sort: str = "newest",  # "newest" | "oldest" | "size"
    skip: int = 0,
    limit: int = 48,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    query = db.query(MediaAsset).filter(_accessible_media_filter(db, current_user))

    if direction == "uploaded":
        query = query.filter(
            MediaAsset.owner_id == current_user.id,
            MediaAsset.source.in_([MediaSource.WALL, MediaSource.DIRECT_UPLOAD]),
        )
    elif direction == "sent":
        query = query.filter(
            MediaAsset.owner_id == current_user.id,
            MediaAsset.source.in_([MediaSource.MESSENGER, MediaSource.ROOM]),
        )
    elif direction == "received":
        query = query.filter(MediaAsset.owner_id != current_user.id)

    if media_type:
        try:
            query = query.filter(MediaAsset.media_type == MediaType(media_type))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Neznámý media_type: {media_type}")

    if source:
        try:
            query = query.filter(MediaAsset.source == MediaSource(source))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Neznámý source: {source}")

    if sort == "oldest":
        query = query.order_by(MediaAsset.created_at.asc())
    elif sort == "size":
        query = query.order_by(MediaAsset.size_bytes.desc())
    else:
        query = query.order_by(MediaAsset.created_at.desc())

    assets = query.offset(skip).limit(min(limit, 200)).all()
    return [_to_out(a, current_user) for a in assets]


@router.get("/{media_id}", response_model=MediaAssetOut)
def get_media(
    media_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    asset = db.query(MediaAsset).filter(
        MediaAsset.id == media_id, _accessible_media_filter(db, current_user)
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Médium nenalezeno")
    return _to_out(asset, current_user)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Smazat může jen vlastník (autor uploadu) nebo moderátor/admin."""
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Médium nenalezeno")

    is_owner = asset.owner_id == current_user.id
    is_staff = current_user.role in (RoleEnum.MODERATOR, RoleEnum.ADMIN)
    if not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="Nemáš oprávnění smazat toto médium")

    # Odpojit navázané zprávy, ať nezůstane viset cizí FK.
    db.query(DirectMessage).filter(DirectMessage.media_id == media_id).update({"media_id": None})
    db.query(RoomMessage).filter(RoomMessage.media_id == media_id).update({"media_id": None})

    media_service.MEDIA_ROOT.joinpath(asset.file_path).unlink(missing_ok=True)
    db.delete(asset)
    db.commit()

    log_event(
        db, LogType.SYSTEM_MEDIA_LOG,
        action="media_deleted",
        actor_user_id=current_user.id,
        target=str(media_id),
        ip_address=request.client.host if request.client else None,
    )
    return None
