from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id.asc()).all()


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    valid_roles = {r.value for r in RoleEnum}
    if payload.role not in valid_roles:
        log_event(
            db, LogType.OPERATION_SYSTEM_LOG_ERROR,
            action="user_role_change_failed_invalid_role",
            actor_user_id=current_user.id,
            target=f"user:{user_id}",
            ip_address=request.client.host if request.client else None,
            meta={"attempted_role": payload.role},
        )
        raise HTTPException(status_code=400, detail=f"role musí být jedna z: {', '.join(valid_roles)}")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        log_event(
            db, LogType.OPERATION_SYSTEM_LOG_ERROR,
            action="user_role_change_failed_user_not_found",
            actor_user_id=current_user.id,
            target=f"user:{user_id}",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    old_role = target_user.role.value
    target_user.role = RoleEnum(payload.role)
    db.commit()
    db.refresh(target_user)

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="user_role_changed",
        actor_user_id=current_user.id,
        target=f"user:{user_id}",
        ip_address=request.client.host if request.client else None,
        meta={"old_role": old_role, "new_role": payload.role},
    )
    return target_user
