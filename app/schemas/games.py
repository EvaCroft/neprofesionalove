from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class GameCreate(BaseModel):
    room_id: int
    type: str = "tic_tac_toe"
    stake: Optional[str] = None  # v16 - volitelný vklad/pot (Decimal jako string), null = bez potu


class GameJoinTeamRequest(BaseModel):
    team: int  # v16 - 1 nebo 2


class GameMove(BaseModel):
    position: int


class GameOut(BaseModel):
    id: int
    room_id: int
    type: str
    status: str
    player1_id: int
    player2_id: Optional[int] = None
    board: List[Optional[str]]
    current_turn_user_id: Optional[int] = None
    winner_user_id: Optional[int] = None
    is_draw: bool
    created_at: datetime
    finished_at: Optional[datetime] = None
    spectator_count: int = 0
    stake: Optional[str] = None
    team1_player_ids: List[int] = []
    team2_player_ids: List[int] = []
    winner_team: Optional[int] = None


class SpectatorOut(BaseModel):
    user_id: int
    started_watching_at: datetime
