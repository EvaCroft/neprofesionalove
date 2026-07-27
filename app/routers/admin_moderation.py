from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.moderation import RoomModerator
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.routers.rooms import _get_room_or_404
from app.schemas import ModeratorAssign

router = APIRouter(prefix="/admin", tags=["admin-moderation"])


@router.post("/moderators", status_code=201)
def assign_moderator(
    payload: ModeratorAssign,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, payload.room_id)
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    existing = (
        db.query(RoomModerator)
        .filter(RoomModerator.room_id == payload.room_id, RoomModerator.moderator_user_id == payload.user_id)
        .first()
    )
    if existing:
        return {"detail": "Už je přiřazen"}

    db.add(RoomModerator(room_id=payload.room_id, moderator_user_id=payload.user_id))
    db.commit()

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="moderator_assigned",
        actor_user_id=current_user.id,
        target=f"room:{payload.room_id}:user:{payload.user_id}",
        ip_address=request.client.host if request.client else None,
    )
    return {"detail": "Přiřazen"}


@router.delete("/moderators/{room_id}/{user_id}", status_code=204)
def unassign_moderator(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(RoomModerator)
        .filter(RoomModerator.room_id == room_id, RoomModerator.moderator_user_id == user_id)
        .first()
    )
    if assignment:
        db.delete(assignment)
        db.commit()
        log_event(
            db, LogType.OPERATION_SYSTEM_LOG,
            action="moderator_unassigned",
            actor_user_id=current_user.id,
            target=f"room:{room_id}:user:{user_id}",
            ip_address=request.client.host if request.client else None,
        )
