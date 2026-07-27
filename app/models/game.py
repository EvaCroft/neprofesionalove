"""
Model Game - obecná herní abstrakce vázaná na místnost. v13 obsahuje jen
piškvorky (TIC_TAC_TOE), 1v1. Board je uložen jako JSON text (9 polí:
"X"/"O"/null), aby šla abstrakce v budoucnu rozšířit o další typy her
beze změny schématu (viz v16 - týmové varianty).
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Text, Boolean, Numeric

from app.db import Base


class GameType(str, enum.Enum):
    TIC_TAC_TOE = "tic_tac_toe"
    TEAM_TIC_TAC_TOE = "team_tic_tac_toe"  # v16 - 2v2 týmová varianta


class GameStatus(str, enum.Enum):
    WAITING_FOR_PLAYER2 = "waiting_for_player2"
    WAITING_FOR_PLAYERS = "waiting_for_players"  # v16 - týmová hra čeká na zaplnění 4 slotů
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    type = Column(Enum(GameType), nullable=False, default=GameType.TIC_TAC_TOE)
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.WAITING_FOR_PLAYER2)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # hraje "X"
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # hraje "O"
    board = Column(Text, nullable=False)  # JSON: 9 polí "X"/"O"/null
    current_turn_user_id = Column(Integer, nullable=True)
    winner_user_id = Column(Integer, nullable=True)  # null dokud FINISHED nebo remíza
    is_draw = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)

    # v16 - volitelný pot/vklad + týmová rotace tahů
    stake_amount = Column(Numeric(precision=18, scale=2), nullable=True)  # vklad na hráče, null = bez potu
    turn_order = Column(Text, nullable=True)  # JSON list user_id, jen pro team_tic_tac_toe
    turn_index = Column(Integer, nullable=False, default=0)
    winner_team = Column(Integer, nullable=True)  # 1 nebo 2, jen pro team_tic_tac_toe (vítěz = "X"/tým1 nebo "O"/tým2)
    reward_settled = Column(Boolean, nullable=False, default=False)  # pojistka proti dvojímu vyplacení potu


class GameTeamPlayer(Base):
    """Členství hráče v týmu u týmové hry (v16). Max 2 hráči na tým (1-2)."""
    __tablename__ = "game_team_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    team = Column(Integer, nullable=False)  # 1 nebo 2
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GameSpectator(Base):
    """Kdo aktuálně sleduje danou hru (v14 - živé sledování, dle konceptu
    'vizualizace jak počet lidí ho sleduje'). Přítomnost záznamu = sleduje;
    unwatch záznam maže (ne soft-delete - spectator count má být přesný
    live snapshot, ne historie)."""
    __tablename__ = "game_spectators"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_watching_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
