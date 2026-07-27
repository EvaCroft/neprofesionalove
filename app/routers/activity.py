"""
Router pro Aktivitu na profilu (v23).

Endpointy:
  GET /activity/{user_id}       - formátovaný výpis aktivity daného uživatele
                                   (guest smí vidět jen veřejně propsané akce)
  GET /activity/settings/me     - moje nastavení, co se propisuje do veřejné Aktivity
  PUT /activity/settings/me     - úprava nastavení

Aktivita čte z existujícího user-logu (OPERATION_USER_LOG / SYSTEM_MEDIA_LOG),
nezavádí žádnou novou logovací cestu - viz app/services/activity_service.py.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.db import get_db
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import ActivityEntryOut, ActivitySettingsOut, ActivitySettingsUpdate
from app.services.activity_service import (
    ACTIVITY_ACTION_KEYS, get_activity_settings, list_activity,
)

router = APIRouter(prefix="/activity", tags=["activity"])
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _optional_user(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    """Stejný vzor jako u Zdi (guest smí číst) - profil aktivity je čitelný
    i bez přihlášení, ale co uvidí, závisí na tom, kdo se dívá."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == int(payload.get("sub"))).first()


@router.get("/{user_id}", response_model=List[ActivityEntryOut])
def read_activity(
    user_id: int,
    limit: int = Query(default=20, le=200),
    viewer: Optional[User] = Depends(_optional_user),
    db: Session = Depends(get_db),
):
    is_privileged = bool(viewer and viewer.role in (RoleEnum.MODERATOR, RoleEnum.ADMIN))
    entries = list_activity(
        db, profile_user_id=user_id,
        viewer_id=viewer.id if viewer else None,
        is_privileged=is_privileged,
        limit=limit,
    )
    return entries


@router.get("/settings/me", response_model=ActivitySettingsOut)
def get_my_activity_settings(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    settings = get_activity_settings(db, current_user.id)
    actions = {key: (settings.visible_actions or {}).get(key, True) for key in ACTIVITY_ACTION_KEYS}
    return ActivitySettingsOut(user_id=current_user.id, visible_actions=actions)


@router.put("/settings/me", response_model=ActivitySettingsOut)
def update_my_activity_settings(
    payload: ActivitySettingsUpdate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    invalid = [k for k in payload.actions if k not in ACTIVITY_ACTION_KEYS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Neznámé akce: {invalid}. Povolené: {list(ACTIVITY_ACTION_KEYS)}")

    settings = get_activity_settings(db, current_user.id)
    current = dict(settings.visible_actions or {})
    current.update(payload.actions)
    settings.visible_actions = current
    db.commit()
    db.refresh(settings)

    actions = {key: current.get(key, True) for key in ACTIVITY_ACTION_KEYS}
    return ActivitySettingsOut(user_id=current_user.id, visible_actions=actions)
