"""
Router Odznaky (v25, viz DEVLOG #044).

Katalog (`Badge`) je guest-friendly ke čtení (`GET /badges`), editace jen
adminem (stejný vzor jako `AppSetting` v `admin.py`). Výběr uživatele
(`UserBadge`) je guest-friendly ke čtení podle `user_id` (stejný vzor jako
Zeď/Aktivita/Události - "veřejný" pohled na cizí profil), zápis jen pro
vlastní účet (`PUT /badges/me`), s aplikačním limitem MAX_USER_BADGES.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.badge import Badge, UserBadge
from app.models.log import LogType
from app.models.user import RoleEnum, User
from app.permissions import require_role
from app.routers.auth import get_current_user
from app.schemas import BadgeCreate, BadgeOut, BadgeUpdate, UserBadgesUpdate

router = APIRouter(prefix="/badges", tags=["badges"])

MAX_USER_BADGES = 5


@router.get("", response_model=List[BadgeOut])
def list_badges(db: Session = Depends(get_db)):
    """Katalog aktivních odznaků, guest-friendly. Neaktivní (adminem
    vypnuté) odznaky se nenabízí k novému výběru, ale u uživatelů, kteří
    už je mají vybrané, zůstávají zobrazené (viz `get_user_badges`)."""
    return (
        db.query(Badge)
        .filter(Badge.is_active.is_(True))
        .order_by(Badge.sort_order.asc())
        .all()
    )


@router.get("/{user_id}", response_model=List[BadgeOut])
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    """Vybrané odznaky konkrétního uživatele, guest-friendly (zobrazení na
    cizím profilu)."""
    keys = [ub.badge_key for ub in db.query(UserBadge).filter(UserBadge.user_id == user_id).all()]
    if not keys:
        return []
    return db.query(Badge).filter(Badge.key.in_(keys)).order_by(Badge.sort_order.asc()).all()


@router.put("/me", response_model=List[BadgeOut])
def set_my_badges(
    payload: UserBadgesUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nastaví kompletní výběr odznaků uživatele (přepíše předchozí výběr,
    ne přidání) - jednodušší kontrakt pro frontend (checkbox grid -> jeden
    PUT s finálním seznamem), stejný vzor jako `WallSettingsUpdate`."""
    keys = list(dict.fromkeys(payload.badge_keys))  # unikátní, zachová pořadí
    if len(keys) > MAX_USER_BADGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max. {MAX_USER_BADGES} odznaků na profil.",
        )
    valid_keys = {
        b.key for b in db.query(Badge).filter(Badge.key.in_(keys)).all()
    }
    unknown = set(keys) - valid_keys
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Neznámé odznaky: {', '.join(sorted(unknown))}",
        )

    db.query(UserBadge).filter(UserBadge.user_id == current_user.id).delete()
    for key in keys:
        db.add(UserBadge(user_id=current_user.id, badge_key=key))
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        actor_user_id=current_user.id, action="badges_updated",
        target=str(current_user.id), ip_address=request.client.host if request.client else None,
        meta={"badge_keys": keys},
    )

    return db.query(Badge).filter(Badge.key.in_(keys)).order_by(Badge.sort_order.asc()).all() if keys else []


# --- Admin CRUD katalogu ---

@router.post("/admin", response_model=BadgeOut, status_code=status.HTTP_201_CREATED)
def admin_create_badge(
    payload: BadgeCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    if db.query(Badge).filter(Badge.key == payload.key).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Odznak s tímto klíčem už existuje.")
    max_order = db.query(Badge).count()
    badge = Badge(key=payload.key, emoji=payload.emoji, name=payload.name, is_active=True, sort_order=max_order)
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return badge


@router.put("/admin/{badge_key}", response_model=BadgeOut)
def admin_update_badge(
    badge_key: str,
    payload: BadgeUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    badge = db.query(Badge).filter(Badge.key == badge_key).first()
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Odznak nenalezen.")
    if payload.emoji is not None:
        badge.emoji = payload.emoji
    if payload.name is not None:
        badge.name = payload.name
    if payload.is_active is not None:
        badge.is_active = payload.is_active
    db.commit()
    db.refresh(badge)
    return badge


@router.delete("/admin/{badge_key}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_badge(
    badge_key: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    """Tvrdé smazání z katalogu smaže i všechny uživatelské výběry tohoto
    odznaku (FK bez cizí historie k zachování) - proto se v praxi
    doporučuje spíš `is_active=false` (skryje z nabídky, ponechá u
    uživatelů, kteří ho už mají)."""
    badge = db.query(Badge).filter(Badge.key == badge_key).first()
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Odznak nenalezen.")
    db.query(UserBadge).filter(UserBadge.badge_key == badge_key).delete()
    db.delete(badge)
    db.commit()
