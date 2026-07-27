"""
Service pro tab "Aktivita" na profilu.

Návrh vychází z toho, co v projektu už existuje: naprostá většina akcí se
už dneska loguje přes `log_event()` do OPERATION_USER_LOG (uživatelský
audit log) a je automaticky zrcadlena do SYSTEM_LOG_FULL / _BACKUP1
(admin log - vidí úplně vše, beze změny). Aktivita na profilu tedy NENÍ
nová logovací cesta - je to jen čitelná, filtrovaná projekce nad logem,
který už existuje.

- ACTIVITY_ACTION_KEYS: registr akcí, které smí být vidět v Aktivitě (ne
  všechno v logu je vhodné ukazovat na profilu - login, chybové akce,
  moderační zásahy nad jinými apod. se sem záměrně nedávají). Stejný vzor
  jako WALL_ACTION_KEYS v post_service.py - použije se i pro FE nastavení
  "co se propisuje dál" (ActivitySettings.visible_actions).
- render_entry(): z LogEntry vyrobí lidsky čitelný český text, s dohledáním
  názvů entit (místnost/událost/soupeř), když je log neobsahuje přímo.
- list_activity(): hlavní čtecí funkce pro endpoint, respektuje viditelnost.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.log import LogEntry, LogType
from app.models.activity_settings import ActivitySettings
from app.models.room import Room
from app.models.event import Event
from app.models.game import Game
from app.models.profile import Profile

# action_key -> lidský popis pro nastavení ("co se propisuje do veřejné Aktivity")
ACTIVITY_ACTION_KEYS = {
    "post_create": "Nový příspěvek na zeď",
    "room_created": "Založení místnosti",
    "room_joined": "Vstup do místnosti",
    "room_left": "Odchod z místnosti",
    "event_created": "Vytvoření události",
    "media_uploaded": "Nahrání fotky/videa",
    "referral_reward_earned": "Odměna za pozvání přes referral",
    "game_move": "Výhra ve hře",
}

# které log_type streamy se prohledávají (aktivita je napříč víc typy, ne jen OPERATION_USER_LOG)
_ACTIVITY_LOG_TYPES = (LogType.OPERATION_USER_LOG, LogType.SYSTEM_MEDIA_LOG)


def get_activity_settings(db: Session, user_id: int) -> ActivitySettings:
    settings = db.query(ActivitySettings).filter(ActivitySettings.user_id == user_id).first()
    if not settings:
        settings = ActivitySettings(user_id=user_id, visible_actions={})
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def is_action_visible(db: Session, user_id: int, action_key: str) -> bool:
    """Chybějící klíč = výchozí viditelné (stejný vzor jako WallSettings)."""
    settings = get_activity_settings(db, user_id)
    actions = settings.visible_actions or {}
    return actions.get(action_key, True)


def _display_name(db: Session, user_id: Optional[int]) -> str:
    if not user_id:
        return "někdo"
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile and profile.display_name:
        return profile.display_name
    return f"Uživatel #{user_id}"


def _target_id(entry: LogEntry) -> Optional[int]:
    """Vytáhne poslední číselnou část z target (\"room:5\" -> 5, \"game:12\" -> 12)."""
    if not entry.target:
        return None
    tail = entry.target.rsplit(":", 1)[-1]
    return int(tail) if tail.isdigit() else None


def render_entry(db: Session, entry: LogEntry) -> Optional[str]:
    """Vyrobí čitelnou českou větu pro danou log položku, nebo None pokud se
    tenhle typ akce v Aktivitě nezobrazuje (ošetřuje i edge-case jako
    nevyhraný game_move)."""
    action = entry.action
    entity_id = _target_id(entry)

    if action == "post_create":
        return "Přidala nový příspěvek na zeď"

    if action == "room_created":
        room = db.query(Room).filter(Room.id == entity_id).first() if entity_id else None
        return f"Založila místnost {room.name}" if room else "Založila novou místnost"

    if action == "room_joined":
        room = db.query(Room).filter(Room.id == entity_id).first() if entity_id else None
        return f"Vstoupila do místnosti {room.name}" if room else "Vstoupila do místnosti"

    if action == "room_left":
        room = db.query(Room).filter(Room.id == entity_id).first() if entity_id else None
        return f"Opustila místnost {room.name}" if room else "Opustila místnost"

    if action == "event_created":
        event = db.query(Event).filter(Event.id == entity_id).first() if entity_id else None
        return f"Vytvořila událost {event.title}" if event else "Vytvořila novou událost"

    if action == "media_uploaded":
        return "Nahrála nové médium do Mých médií"

    if action == "referral_reward_earned":
        amount = (entry.meta and _meta_get(entry.meta, "amount")) or None
        return f"Pozvala nového člena přes referral kód (+{amount} kr.)" if amount else \
            "Pozvala nového člena přes referral kód"

    if action == "game_move":
        # v logu je game_move za KAŽDÝ tah - do Aktivity patří jen ten,
        # kterým aktér hru vyhrál (winner_user_id == actor).
        game = db.query(Game).filter(Game.id == entity_id).first() if entity_id else None
        if not game or game.winner_user_id != entry.actor_user_id:
            return None
        opponent_id = game.player2_id if game.winner_user_id == game.player1_id else game.player1_id
        return f"Vyhrála hru proti {_display_name(db, opponent_id)}"

    return None


def _meta_get(meta_json: str, key: str):
    import json
    try:
        return json.loads(meta_json).get(key)
    except Exception:
        return None


def list_activity(db: Session, profile_user_id: int, viewer_id: Optional[int], is_privileged: bool, limit: int = 50):
    """Vrátí formátovaný seznam aktivit `profile_user_id`.

    - Majitel profilu (viewer_id == profile_user_id) a Moderator+/Admin
      (is_privileged) vidí VŠECHNO, co je v ACTIVITY_ACTION_KEYS, bez ohledu
      na ActivitySettings (to je jen "propis DÁL", ne skrytí sama sobě/mod).
    - Ostatní diváci vidí jen akce, které má majitel profilu v
      ActivitySettings povolené (chybějící klíč = default viditelné).
    """
    limit = min(limit, 200)
    is_owner_or_privileged = is_privileged or viewer_id == profile_user_id

    query = (
        db.query(LogEntry)
        .filter(LogEntry.actor_user_id == profile_user_id)
        .filter(LogEntry.log_type.in_(_ACTIVITY_LOG_TYPES))
        .filter(LogEntry.action.in_(list(ACTIVITY_ACTION_KEYS)))
        .order_by(LogEntry.timestamp.desc())
        .limit(limit * 3)  # rezerva, protože část (game_move bez výhry, chybějící entity) se odfiltruje až při renderu
    )

    results = []
    for entry in query.all():
        if not is_owner_or_privileged and not is_action_visible(db, profile_user_id, entry.action):
            continue
        text = render_entry(db, entry)
        if not text:
            continue
        results.append({"action": entry.action, "timestamp": entry.timestamp, "text": text})
        if len(results) >= limit:
            break

    return results
