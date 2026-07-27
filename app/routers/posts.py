"""
Router pro příspěvky/zeď (v20+, "Systém příspěvků").

Endpointy:
  POST   /posts                       - vytvořit vlastní post (na svou zeď nebo zeď jiného uživatele)
  GET    /posts/wall/{user_id}        - zeď daného uživatele (respektuje visibility)
  PATCH  /posts/{post_id}             - úprava vlastního postu (text/visibility)
  DELETE /posts/{post_id}             - smazání (autor, majitel zdi, nebo moderator+)
  GET    /posts/settings/me           - moje nastavení propisu akcí na zeď
  PUT    /posts/settings/me           - úprava nastavení propisu
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from fastapi.security import OAuth2PasswordBearer

from app.models.post import Post, PostOrigin, PostVisibility
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.auth import decode_access_token
from app.schemas import PostCreate, PostUpdate, PostOut, WallSettingsOut, WallSettingsUpdate
from app.services.post_service import (
    WALL_ACTION_KEYS, get_wall_settings, visible_to,
)

router = APIRouter(prefix="/posts", tags=["posts"])

_optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(_optional_oauth2), db: Session = Depends(get_db)
) -> Optional[User]:
    """Jako get_current_user, ale bez tokenu (guest) vrátí None místo 401 -
    použito na /posts/wall/{user_id}, kterou smí prohlížet i guest."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()


def _parse_visibility(value: str) -> PostVisibility:
    try:
        return PostVisibility(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Neplatná visibility: {value}. Povolené: public, friends, private")


@router.post("", response_model=PostOut)
def create_post(
    payload: PostCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    if not payload.text and not payload.media_id:
        raise HTTPException(status_code=400, detail="Post musí mít text nebo médium")

    post = Post(
        author_id=current_user.id,
        target_user_id=payload.target_user_id or current_user.id,
        text=payload.text,
        media_id=payload.media_id,
        origin=PostOrigin.USER_POST,
        visibility=_parse_visibility(payload.visibility),
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    log_event(
        db, LogType.OPERATION_USER_LOG, action="post_create",
        actor_user_id=current_user.id, target=str(post.id),
        ip_address=request.client.host if request.client else None,
    )
    return post


@router.get("/wall/{user_id}", response_model=List[PostOut])
def get_wall(
    user_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Zeď uživatele - veřejně dostupné (guest vidí jen public posty)."""
    viewer_id = current_user.id if current_user else None
    posts = (
        db.query(Post)
        .filter(Post.target_user_id == user_id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [p for p in posts if visible_to(p, viewer_id)]


@router.patch("/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    payload: PostUpdate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nenalezen")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Pouze autor může post upravit")

    if payload.text is not None:
        post.text = payload.text
    if payload.visibility is not None:
        post.visibility = _parse_visibility(payload.visibility)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nenalezen")

    is_owner_party = current_user.id in (post.author_id, post.target_user_id)
    is_staff = current_user.role in (RoleEnum.MODERATOR, RoleEnum.ADMIN)
    if not is_owner_party and not is_staff:
        raise HTTPException(status_code=403, detail="Nemáte oprávnění smazat tento post")

    db.delete(post)
    db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG, action="post_delete",
        actor_user_id=current_user.id, target=str(post_id),
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "deleted"}


@router.get("/settings/me", response_model=WallSettingsOut)
def get_my_wall_settings(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    settings = get_wall_settings(db, current_user.id)
    # doplnit chybějící klíče výchozí hodnotou True, ať FE vidí kompletní seznam
    actions = {key: (settings.auto_post_actions or {}).get(key, True) for key in WALL_ACTION_KEYS}
    return WallSettingsOut(user_id=current_user.id, auto_post_actions=actions)


@router.put("/settings/me", response_model=WallSettingsOut)
def update_my_wall_settings(
    payload: WallSettingsUpdate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    invalid = [k for k in payload.actions if k not in WALL_ACTION_KEYS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Neznámé akce: {invalid}. Povolené: {list(WALL_ACTION_KEYS)}")

    settings = get_wall_settings(db, current_user.id)
    current = dict(settings.auto_post_actions or {})
    current.update(payload.actions)
    settings.auto_post_actions = current
    db.commit()
    db.refresh(settings)

    actions = {key: current.get(key, True) for key in WALL_ACTION_KEYS}
    return WallSettingsOut(user_id=current_user.id, auto_post_actions=actions)
