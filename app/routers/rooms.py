from typing import List
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.profile import Profile
from app.models.room import Room, RoomMembership, RoomType
from app.models.room_message import RoomMessage
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import RoomOut, RoomCreate, RoomMessageCreate, RoomMessageOut
from app.services import credit_service
from app.services.credit_service import InsufficientFundsError

router = APIRouter(prefix="/rooms", tags=["rooms"])

MAX_WALL_LINES = 2  # dle konceptu: zpráva na chat-wall max 2 řádky


def _get_membership(db: Session, room_id: int, user_id: int) -> RoomMembership | None:
    return (
        db.query(RoomMembership)
        .filter(RoomMembership.room_id == room_id, RoomMembership.user_id == user_id)
        .first()
    )


def _is_member(db: Session, room_id: int, user_id: int) -> bool:
    m = _get_membership(db, room_id, user_id)
    return m is not None and not m.banned


def _require_owner(db: Session, room: Room, current_user: User):
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Jen vlastník místnosti může tuto akci provést")


def _get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Místnost nenalezena")
    return room


def _room_out(db: Session, room: Room) -> RoomOut:
    member_count = db.query(RoomMembership).filter(RoomMembership.room_id == room.id).count()
    return RoomOut(
        id=room.id, name=room.name, type=room.type.value, owner_id=room.owner_id,
        created_at=room.created_at, member_count=member_count, entry_fee=str(room.entry_fee),
    )


@router.post("", response_model=RoomOut, status_code=201)
def create_room(
    payload: RoomCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    if payload.type not in ("public", "private"):
        raise HTTPException(status_code=400, detail="type musí být 'public' nebo 'private'")
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Název místnosti nemůže být prázdný")

    try:
        entry_fee = Decimal(payload.entry_fee)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="entry_fee musí být platné číslo")
    if entry_fee < 0:
        raise HTTPException(status_code=400, detail="entry_fee nemůže být záporné")

    room = Room(
        name=payload.name.strip(),
        type=RoomType.PUBLIC if payload.type == "public" else RoomType.PRIVATE,
        owner_id=current_user.id,
        entry_fee=entry_fee,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # vlastník je automaticky členem (bez placení vlastního vstupného)
    db.add(RoomMembership(room_id=room.id, user_id=current_user.id))
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_created",
        actor_user_id=current_user.id,
        target=f"room:{room.id}",
        ip_address=request.client.host if request.client else None,
        meta={"name": room.name, "type": payload.type, "entry_fee": str(entry_fee)},
    )

    return _room_out(db, room)


@router.get("", response_model=List[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    """Seznam místností - veřejně dostupné i pro guesty (bez auth)."""
    rooms = db.query(Room).all()
    return [_room_out(db, r) for r in rooms]


@router.post("/{room_id}/join", status_code=204)
def join_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    ip = request.client.host if request.client else None

    if room.type == RoomType.PRIVATE:
        # v4/v5: bez obecného invite systému - soukromé místnosti zatím
        # nejdou joinnout samoobslužně (vlastník přidává členy jinak - backlog).
        raise HTTPException(status_code=403, detail="Do soukromé místnosti nelze vstoupit bez pozvání")

    membership = _get_membership(db, room_id, current_user.id)
    if membership and membership.banned:
        raise HTTPException(status_code=403, detail="Byl(a) jsi z této místnosti vykázán(a)")
    if membership:
        return  # idempotentní - už je členem

    if room.entry_fee and Decimal(room.entry_fee) > 0:
        try:
            credit_service.charge_room_fee(db, current_user.id, room.owner_id, Decimal(room.entry_fee), room_id)
        except InsufficientFundsError as e:
            raise HTTPException(status_code=402, detail=str(e))

    db.add(RoomMembership(room_id=room_id, user_id=current_user.id))
    db.commit()
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_joined",
        actor_user_id=current_user.id,
        target=f"room:{room_id}",
        ip_address=ip,
        meta={"entry_fee": str(room.entry_fee)} if room.entry_fee else None,
    )


@router.post("/{room_id}/leave", status_code=204)
def leave_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    membership = _get_membership(db, room_id, current_user.id)
    if membership and membership.banned:
        # kicknutý uživatel nemůže "odejít" a tím si smazat ban - no-op
        return
    if membership:
        from datetime import datetime, timezone
        joined_at = membership.joined_at
        if joined_at and joined_at.tzinfo is None:
            joined_at = joined_at.replace(tzinfo=timezone.utc)
        if joined_at:
            elapsed_minutes = int((datetime.now(timezone.utc) - joined_at).total_seconds() // 60)
            if elapsed_minutes > 0:
                profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
                if profile:
                    profile.chat_minutes = (profile.chat_minutes or 0) + elapsed_minutes

        db.delete(membership)
        db.commit()
        log_event(
            db, LogType.OPERATION_USER_LOG,
            action="room_left",
            actor_user_id=current_user.id,
            target=f"room:{room_id}",
            ip_address=request.client.host if request.client else None,
        )


@router.post("/{room_id}/messages", response_model=RoomMessageOut, status_code=201)
def post_room_message(
    room_id: int,
    payload: RoomMessageCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    ip = request.client.host if request.client else None

    if not _is_member(db, room_id, current_user.id):
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="room_message_failed_not_member",
            actor_user_id=current_user.id,
            target=f"room:{room_id}",
            ip_address=ip,
        )
        raise HTTPException(status_code=403, detail="Pro psaní do místnosti musíš být členem")

    membership = _get_membership(db, room_id, current_user.id)
    if membership.muted:
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="room_message_failed_muted",
            actor_user_id=current_user.id,
            target=f"room:{room_id}",
            ip_address=ip,
        )
        raise HTTPException(status_code=403, detail="Jsi umlčen(a) v této místnosti")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Zpráva nemůže být prázdná")

    line_count = len(text.splitlines())
    if line_count > MAX_WALL_LINES:
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="room_message_failed_too_many_lines",
            actor_user_id=current_user.id,
            target=f"room:{room_id}",
            ip_address=ip,
            meta={"line_count": line_count},
        )
        raise HTTPException(
            status_code=400,
            detail=f"Zpráva na wall může mít max {MAX_WALL_LINES} řádky",
        )

    message = RoomMessage(room_id=room_id, user_id=current_user.id, text=text)
    db.add(message)
    db.commit()
    db.refresh(message)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_message_posted",
        actor_user_id=current_user.id,
        target=f"room:{room_id}",
        ip_address=ip,
        meta={"message_id": message.id},
    )
    return message


@router.get("/{room_id}/messages", response_model=List[RoomMessageOut])
def get_room_messages(
    room_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    if not _is_member(db, room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro čtení historie musíš být členem")

    return (
        db.query(RoomMessage)
        .filter(RoomMessage.room_id == room_id)
        .order_by(RoomMessage.sent_at.asc())
        .all()
    )


@router.post("/{room_id}/kick/{user_id}", status_code=204)
def kick_member(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    _require_owner(db, room, current_user)

    if user_id == room.owner_id:
        raise HTTPException(status_code=400, detail="Vlastníka nelze vyhodit z vlastní místnosti")

    membership = _get_membership(db, room_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Uživatel není členem místnosti")

    membership.banned = True
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_member_kicked",
        actor_user_id=current_user.id,
        target=f"room:{room_id}:user:{user_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/{room_id}/mute/{user_id}", status_code=204)
def mute_member(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    _require_owner(db, room, current_user)

    membership = _get_membership(db, room_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Uživatel není členem místnosti")

    membership.muted = True
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_member_muted",
        actor_user_id=current_user.id,
        target=f"room:{room_id}:user:{user_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/{room_id}/unmute/{user_id}", status_code=204)
def unmute_member(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    _require_owner(db, room, current_user)

    membership = _get_membership(db, room_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Uživatel není členem místnosti")

    membership.muted = False
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_member_unmuted",
        actor_user_id=current_user.id,
        target=f"room:{room_id}:user:{user_id}",
        ip_address=request.client.host if request.client else None,
    )
