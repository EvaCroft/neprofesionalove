from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.settings import AppSetting
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import SettingOut, SettingUpdate

router = APIRouter(prefix="/admin", tags=["admin-settings"])


@router.get("/settings", response_model=List[SettingOut])
def list_settings(
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(AppSetting).order_by(AppSetting.key.asc()).all()


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    payload: SettingUpdate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        setting = AppSetting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()
    db.refresh(setting)

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="setting_updated",
        actor_user_id=current_user.id,
        target=key,
        ip_address=request.client.host if request.client else None,
        meta={"value": payload.value},
    )
    return setting
