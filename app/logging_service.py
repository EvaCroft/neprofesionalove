"""
Centrální logovací služba. Všechny endpointy v projektu volají log_event()
místo přímého zápisu do DB, aby byl formát logů konzistentní napříč
celým systémem (kdo/co/kdy/kde/koho to ovlivnilo).
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.log import LogEntry, LogType


def log_event(
    db: Session,
    log_type: LogType,
    action: str,
    actor_user_id: Optional[int] = None,
    target: Optional[str] = None,
    ip_address: Optional[str] = None,
    meta: Optional[dict] = None,
) -> LogEntry:
    """Zapíše jeden log záznam do jeho specifického streamu a zároveň jej
    zrcadlí do SYSTEM_LOG_FULL (kompletní audit trail všech operací nad
    platformou) a SYSTEM_LOG_FULL_BACKUP1 (redundantní kopie). Mirror se
    přeskočí, když log_type UŽ JE jeden z těch dvou (jinak nekonečná smyčka)."""
    meta_json = json.dumps(meta, ensure_ascii=False) if meta else None

    entry = LogEntry(
        log_type=log_type,
        action=action,
        actor_user_id=actor_user_id,
        target=target,
        ip_address=ip_address,
        meta=meta_json,
    )
    db.add(entry)

    if log_type not in (LogType.SYSTEM_LOG_FULL, LogType.SYSTEM_LOG_FULL_BACKUP1):
        db.add(LogEntry(
            log_type=LogType.SYSTEM_LOG_FULL, action=action, actor_user_id=actor_user_id,
            target=target, ip_address=ip_address, meta=meta_json,
        ))
        db.add(LogEntry(
            log_type=LogType.SYSTEM_LOG_FULL_BACKUP1, action=action, actor_user_id=actor_user_id,
            target=target, ip_address=ip_address, meta=meta_json,
        ))

    db.commit()
    db.refresh(entry)
    return entry
