from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.moderation import RoomModerator, UserReport, ReportTargetType, ReportStatus
from app.models.room import Room, RoomMembership
from app.models.room_message import RoomMessage
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.routers.rooms import _get_membership, _get_room_or_404
from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/moderation", tags=["moderation"])


def _is_assigned_moderator(db: Session, room_id: int, user_id: int) -> bool:
    return (
        db.query(RoomModerator)
        .filter(RoomModerator.room_id == room_id, RoomModerator.moderator_user_id == user_id)
        .first()
        is not None
    )


def _require_room_authority(db: Session, room: Room, current_user: User):
    """Povolí vlastníka místnosti, přiřazeného moderátora, nebo admina."""
    if current_user.role == RoleEnum.ADMIN:
        return
    if room.owner_id == current_user.id:
        return
    if current_user.role == RoleEnum.MODERATOR and _is_assigned_moderator(db, room.id, current_user.id):
        return
    raise HTTPException(
        status_code=403,
        detail="Vyžadován vlastník místnosti, přiřazený moderátor, nebo admin",
    )


@router.post("/reports", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    if payload.target_type not in ("room_message", "user"):
        raise HTTPException(status_code=400, detail="target_type musí být 'room_message' nebo 'user'")
    if not payload.reason.strip():
        raise HTTPException(status_code=400, detail="Reason nemůže být prázdný")

    report = UserReport(
        reporter_id=current_user.id,
        target_type=ReportTargetType(payload.target_type),
        target_id=payload.target_id,
        room_id=payload.room_id,
        reason=payload.reason.strip(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="report_created",
        actor_user_id=current_user.id,
        target=f"{payload.target_type}:{payload.target_id}",
        ip_address=request.client.host if request.client else None,
    )
    return report


@router.get("/reports", response_model=List[ReportOut])
def list_reports(
    status: Optional[str] = None,
    current_user: User = Depends(require_role(RoleEnum.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Admin vidí všechny reporty. Moderator jen reporty vázané na jím
    spravované místnosti (room_id v RoomModerator) nebo reporty bez room_id
    vázané na jeho vlastní místnosti jako owner nejsou zahrnuty zde (owner
    má vlastní pohled - backlog)."""
    query = db.query(UserReport)

    if current_user.role != RoleEnum.ADMIN:
        assigned_room_ids = [
            rm.room_id for rm in
            db.query(RoomModerator).filter(RoomModerator.moderator_user_id == current_user.id).all()
        ]
        query = query.filter(UserReport.room_id.in_(assigned_room_ids)) if assigned_room_ids else query.filter(False)

    if status:
        if status not in ("open", "resolved"):
            raise HTTPException(status_code=400, detail="status musí být 'open' nebo 'resolved'")
        query = query.filter(UserReport.status == ReportStatus(status))

    return query.order_by(UserReport.created_at.desc()).all()


@router.put("/reports/{report_id}/resolve", response_model=ReportOut)
def resolve_report(
    report_id: int,
    current_user: User = Depends(require_role(RoleEnum.MODERATOR)),
    db: Session = Depends(get_db),
):
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report nenalezen")

    if current_user.role != RoleEnum.ADMIN:
        if not report.room_id or not _is_assigned_moderator(db, report.room_id, current_user.id):
            raise HTTPException(status_code=403, detail="Nejsi moderátor přiřazený k této místnosti")

    report.status = ReportStatus.RESOLVED
    db.commit()
    db.refresh(report)
    return report


@router.delete("/messages/{message_id}", status_code=204)
def delete_room_message(
    message_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.MODERATOR)),
    db: Session = Depends(get_db),
):
    message = db.query(RoomMessage).filter(RoomMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Zpráva nenalezena")

    room = _get_room_or_404(db, message.room_id)
    _require_room_authority(db, room, current_user)

    db.delete(message)
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_message_deleted_by_moderator",
        actor_user_id=current_user.id,
        target=f"room:{room.id}:message:{message_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/rooms/{room_id}/mute/{user_id}", status_code=204)
def moderator_mute(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.MODERATOR)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    _require_room_authority(db, room, current_user)

    membership = _get_membership(db, room_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Uživatel není členem místnosti")

    membership.muted = True
    db.commit()
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_member_muted_by_moderator",
        actor_user_id=current_user.id,
        target=f"room:{room_id}:user:{user_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/rooms/{room_id}/ban/{user_id}", status_code=204)
def moderator_ban(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.MODERATOR)),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    _require_room_authority(db, room, current_user)

    if user_id == room.owner_id:
        raise HTTPException(status_code=400, detail="Vlastníka místnosti nelze banovat")

    membership = _get_membership(db, room_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Uživatel není členem místnosti")

    membership.banned = True
    db.commit()
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="room_member_banned_by_moderator",
        actor_user_id=current_user.id,
        target=f"room:{room_id}:user:{user_id}",
        ip_address=request.client.host if request.client else None,
    )
