"""
Service pro Post/zeď.

- create_post_from_action(): volají jiné servisy/routery (media, events,...)
  po dokončení akce, pokud ji chce autor propsat na zeď. Sama respektuje
  nastavení uživatele (WallSettings.auto_post_actions).
- visible_to(): jednotné pravidlo viditelnosti postu pro daného diváka,
  použité v routeru při listování zdi.

Poznámka k "friends": systém přátel není v MVP implementovaný, takže
visibility=FRIENDS se dokud nevznikne, chová jako PRIVATE (viditelné jen
autorovi a majiteli zdi). Až přátelství vznikne, stačí upravit visible_to().
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.post import Post, PostOrigin, PostVisibility
from app.models.wall_settings import WallSettings

# Registr akcí, které lze propisovat na zeď + human-readable popis (pro FE nastavení).
WALL_ACTION_KEYS = {
    "media_upload": "Nahrání fotky/videa na zeď",
    "event_created": "Založení události",
}


def get_wall_settings(db: Session, user_id: int) -> WallSettings:
    settings = db.query(WallSettings).filter(WallSettings.user_id == user_id).first()
    if not settings:
        settings = WallSettings(user_id=user_id, auto_post_actions={})
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def is_action_enabled(db: Session, user_id: int, action_key: str) -> bool:
    """Chybějící klíč = výchozí zapnuto (stejný vzor jako field_visibility)."""
    settings = get_wall_settings(db, user_id)
    actions = settings.auto_post_actions or {}
    return actions.get(action_key, True)


def create_post_from_action(
    db: Session,
    actor_id: int,
    action_key: str,
    text: Optional[str] = None,
    media_id: Optional[int] = None,
    target_user_id: Optional[int] = None,
    visibility: PostVisibility = PostVisibility.PUBLIC,
) -> Optional[Post]:
    """Vytvoří SYSTEM_GENERATED post za akci `action_key`, pokud ji má
    uživatel zapnutou v nastavení. Vrací None, pokud propis je vypnutý."""
    if not is_action_enabled(db, actor_id, action_key):
        return None

    post = Post(
        author_id=actor_id,
        target_user_id=target_user_id or actor_id,
        text=text,
        media_id=media_id,
        origin=PostOrigin.SYSTEM_GENERATED,
        source_action=action_key,
        visibility=visibility,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def visible_to(post: Post, viewer_id: Optional[int]) -> bool:
    """Smí `viewer_id` tenhle post vidět?"""
    if viewer_id is not None and viewer_id in (post.author_id, post.target_user_id):
        return True  # autor a majitel zdi vidí vždy
    if post.visibility == PostVisibility.PUBLIC:
        return True
    return False  # FRIENDS i PRIVATE - dokud není systém přátel, jen autor/majitel
