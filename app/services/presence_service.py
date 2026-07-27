"""
Presence service (v26) - "je online", "co dělá" a hodiny v chatu se
NEPOČÍTAJÍ přes heartbeat (žádný periodický ping z frontendu), ale
odvozují se live z už existujících dat - na žádost uživatele:

- Online/offline: poslední `LogEntry.actor_user_id == user_id` (libovolný
  typ) do ONLINE_THRESHOLD_MINUTES stará → online, jinak offline
  (`last_active_at` = čas toho posledního záznamu).
- current_activity: pokud je uživatel online A zároveň členem nějaké
  `RoomMembership` → "chatuje" (+ název místnosti); pokud je online A má
  rozehranou/čekající `Game` (1v1 i týmovou) → "hraje". Priorita hra >
  chat (aktivnější akce), pokud by nastaly obě zároveň.
- Hodiny v chatu: NEpočítané zpětně z historie (rozhodnutí u #044) - nový
  sloupec `Profile.chat_minutes` se navyšuje při `POST /rooms/{id}/leave`
  o (teď - joined_at), tedy jen pro pobyty v místnosti, které začaly po
  nasazení v26 dopředu.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus, GameTeamPlayer
from app.models.log import LogEntry
from app.models.room import Room, RoomMembership

ONLINE_THRESHOLD_MINUTES = 10

ACTIVE_GAME_STATUSES = [
    GameStatus.WAITING_FOR_PLAYER2,
    GameStatus.WAITING_FOR_PLAYERS,
    GameStatus.IN_PROGRESS,
]


def get_presence(db: Session, user_id: int) -> dict:
    last_log = (
        db.query(LogEntry)
        .filter(LogEntry.actor_user_id == user_id)
        .order_by(LogEntry.timestamp.desc())
        .first()
    )
    last_active_at = last_log.timestamp if last_log else None
    if last_active_at and last_active_at.tzinfo is None:
        last_active_at = last_active_at.replace(tzinfo=timezone.utc)
    is_online = bool(
        last_active_at
        and last_active_at >= datetime.now(timezone.utc) - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    )

    activity = None
    activity_detail = None

    if is_online:
        active_game = (
            db.query(Game)
            .filter(
                Game.status.in_(ACTIVE_GAME_STATUSES),
                (Game.player1_id == user_id) | (Game.player2_id == user_id),
            )
            .first()
        )
        if not active_game:
            team_membership = (
                db.query(GameTeamPlayer)
                .join(Game, Game.id == GameTeamPlayer.game_id)
                .filter(GameTeamPlayer.user_id == user_id, Game.status.in_(ACTIVE_GAME_STATUSES))
                .first()
            )
            if team_membership:
                active_game = db.query(Game).filter(Game.id == team_membership.game_id).first()

        if active_game:
            activity = "playing"
        else:
            membership = db.query(RoomMembership).filter(RoomMembership.user_id == user_id).first()
            if membership:
                room = db.query(Room).filter(Room.id == membership.room_id).first()
                activity = "chatting"
                activity_detail = room.name if room else None

    return {
        "is_online": is_online,
        "last_active_at": last_active_at,
        "activity": activity,
        "activity_detail": activity_detail,
    }
