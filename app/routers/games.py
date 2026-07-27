import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.game import Game, GameType, GameStatus, GameSpectator, GameTeamPlayer
from app.models.user import User, RoleEnum
from app.models.wallet import TransactionType
from app.permissions import require_role
from app.routers.rooms import _get_room_or_404, _is_member
from app.schemas import GameCreate, GameJoinTeamRequest, GameMove, GameOut, SpectatorOut
from app.services import credit_service, game_service
from app.services.credit_service import InsufficientFundsError

router = APIRouter(prefix="/games", tags=["games"])


def _team_ids(db: Session, game_id: int, team: int) -> List[int]:
    rows = (
        db.query(GameTeamPlayer)
        .filter(GameTeamPlayer.game_id == game_id, GameTeamPlayer.team == team)
        .order_by(GameTeamPlayer.joined_at.asc())
        .all()
    )
    return [r.user_id for r in rows]


def _game_out(db: Session, game: Game) -> GameOut:
    spectator_count = db.query(GameSpectator).filter(GameSpectator.game_id == game.id).count()
    team1_ids = _team_ids(db, game.id, 1) if game.type == GameType.TEAM_TIC_TAC_TOE else []
    team2_ids = _team_ids(db, game.id, 2) if game.type == GameType.TEAM_TIC_TAC_TOE else []
    return GameOut(
        id=game.id, room_id=game.room_id, type=game.type.value, status=game.status.value,
        player1_id=game.player1_id, player2_id=game.player2_id,
        board=game_service.board_from_json(game.board),
        current_turn_user_id=game.current_turn_user_id, winner_user_id=game.winner_user_id,
        is_draw=game.is_draw, created_at=game.created_at, finished_at=game.finished_at,
        spectator_count=spectator_count,
        stake=str(game.stake_amount) if game.stake_amount is not None else None,
        team1_player_ids=team1_ids, team2_player_ids=team2_ids,
        winner_team=game.winner_team,
    )


def _get_game_or_404(db: Session, game_id: int) -> Game:
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Hra nenalezena")
    return game


def _parse_stake(stake: str) -> Decimal:
    try:
        amount = Decimal(stake)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=400, detail="Neplatná hodnota vkladu")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Vklad musí být kladný")
    return amount


@router.post("", response_model=GameOut, status_code=201)
def create_game(
    payload: GameCreate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, payload.room_id)
    if not _is_member(db, payload.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro založení hry musíš být členem místnosti")
    if payload.type not in (GameType.TIC_TAC_TOE.value, GameType.TEAM_TIC_TAC_TOE.value):
        raise HTTPException(status_code=400, detail="Zatím podporováno jen 'tic_tac_toe' a 'team_tic_tac_toe'")

    stake_amount = None
    if payload.stake is not None:
        stake_amount = _parse_stake(payload.stake)
        try:
            credit_service.withdraw(
                db, current_user.id, stake_amount, TransactionType.GAME_STAKE_OUT,
                reason="vklad do hry (založení)", actor_user_id=current_user.id,
            )
        except InsufficientFundsError:
            raise HTTPException(status_code=402, detail="Nedostatečný zůstatek pro vklad do hry")

    game_type = GameType(payload.type)
    game = Game(
        room_id=payload.room_id,
        type=game_type,
        status=GameStatus.WAITING_FOR_PLAYERS if game_type == GameType.TEAM_TIC_TAC_TOE else GameStatus.WAITING_FOR_PLAYER2,
        player1_id=current_user.id,
        board=game_service.board_to_json(game_service.empty_board()),
        stake_amount=stake_amount,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    if game_type == GameType.TEAM_TIC_TAC_TOE:
        db.add(GameTeamPlayer(game_id=game.id, user_id=current_user.id, team=1))
        db.commit()

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="game_created",
        actor_user_id=current_user.id,
        target=f"room:{payload.room_id}:game:{game.id}",
        meta={"type": game_type.value, "stake": str(stake_amount) if stake_amount else None},
    )
    return _game_out(db, game)


@router.post("/{game_id}/join", response_model=GameOut)
def join_game(
    game_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)
    if game.type != GameType.TIC_TAC_TOE:
        raise HTTPException(status_code=400, detail="Pro týmovou hru použij /games/{game_id}/join-team")
    if not _is_member(db, game.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro připojení do hry musíš být členem místnosti")
    if game.status != GameStatus.WAITING_FOR_PLAYER2:
        raise HTTPException(status_code=400, detail=f"Hra už není ve stavu čekání na hráče (je '{game.status.value}')")
    if game.player1_id == current_user.id:
        raise HTTPException(status_code=400, detail="Nemůžeš hrát sám proti sobě")

    if game.stake_amount is not None:
        try:
            credit_service.withdraw(
                db, current_user.id, Decimal(game.stake_amount), TransactionType.GAME_STAKE_OUT,
                reason="vklad do hry (připojení)", actor_user_id=current_user.id,
            )
        except InsufficientFundsError:
            raise HTTPException(status_code=402, detail="Nedostatečný zůstatek pro vklad do hry")

    game.player2_id = current_user.id
    game.status = GameStatus.IN_PROGRESS
    game.current_turn_user_id = game.player1_id  # X (zakladatel) začíná
    db.commit()
    db.refresh(game)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="game_joined",
        actor_user_id=current_user.id,
        target=f"game:{game_id}",
    )
    return _game_out(db, game)


@router.post("/{game_id}/join-team", response_model=GameOut)
def join_team_game(
    game_id: int,
    payload: GameJoinTeamRequest,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)
    if game.type != GameType.TEAM_TIC_TAC_TOE:
        raise HTTPException(status_code=400, detail="Tato hra není 2v2 týmová - použij /games/{game_id}/join")
    if not _is_member(db, game.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro připojení do hry musíš být členem místnosti")
    if game.status != GameStatus.WAITING_FOR_PLAYERS:
        raise HTTPException(status_code=400, detail=f"Hra už není ve stavu čekání na hráče (je '{game.status.value}')")
    if payload.team not in (1, 2):
        raise HTTPException(status_code=400, detail="team musí být 1 nebo 2")

    already_in = (
        db.query(GameTeamPlayer)
        .filter(GameTeamPlayer.game_id == game_id, GameTeamPlayer.user_id == current_user.id)
        .first()
    )
    if already_in:
        raise HTTPException(status_code=400, detail="Už jsi v této hře")

    team_members = _team_ids(db, game_id, payload.team)
    if len(team_members) >= 2:
        raise HTTPException(status_code=400, detail=f"Tým {payload.team} je už plný")

    if game.stake_amount is not None:
        try:
            credit_service.withdraw(
                db, current_user.id, Decimal(game.stake_amount), TransactionType.GAME_STAKE_OUT,
                reason="vklad do hry (připojení)", actor_user_id=current_user.id,
            )
        except InsufficientFundsError:
            raise HTTPException(status_code=402, detail="Nedostatečný zůstatek pro vklad do hry")

    db.add(GameTeamPlayer(game_id=game_id, user_id=current_user.id, team=payload.team))
    db.commit()

    team1_ids = _team_ids(db, game_id, 1)
    team2_ids = _team_ids(db, game_id, 2)
    if len(team1_ids) == 2 and len(team2_ids) == 2:
        order = game_service.build_turn_order(team1_ids, team2_ids)
        game.turn_order = json.dumps(order)
        game.turn_index = 0
        game.current_turn_user_id = order[0]
        game.status = GameStatus.IN_PROGRESS
        db.commit()

    db.refresh(game)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="game_team_joined",
        actor_user_id=current_user.id,
        target=f"game:{game_id}",
        meta={"team": payload.team},
    )
    return _game_out(db, game)


def _settle_pot(db: Session, game: Game, result: str, all_participant_ids: List[int], winner_ids: List[int]):
    """Vyplatí/vrátí pot po skončení hry. Idempotentní přes reward_settled.
    Draw -> každému účastníkovi vrácen jeho vklad. Výhra -> pot rozdělen
    rovnoměrně mezi vítěze. Bez potu (stake_amount None) se nic neděje."""
    if game.stake_amount is None or game.reward_settled:
        return
    stake = Decimal(game.stake_amount)
    if result == "draw":
        for uid in all_participant_ids:
            credit_service.deposit(
                db, uid, stake, TransactionType.GAME_STAKE_REFUND,
                reason=f"remíza - vrácení vkladu (hra #{game.id})", actor_user_id=uid,
            )
    else:
        pot = stake * len(all_participant_ids)
        share = pot / len(winner_ids)
        for uid in winner_ids:
            credit_service.deposit(
                db, uid, share, TransactionType.GAME_STAKE_IN,
                reason=f"výhra potu (hra #{game.id})", actor_user_id=uid,
            )
    game.reward_settled = True


@router.post("/{game_id}/move", response_model=GameOut)
def make_move(
    game_id: int,
    payload: GameMove,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)

    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail=f"Hra není 'in_progress' (je '{game.status.value}')")

    is_team_game = game.type == GameType.TEAM_TIC_TAC_TOE

    if is_team_game:
        turn_order = json.loads(game.turn_order)
        if current_user.id not in turn_order:
            raise HTTPException(status_code=403, detail="Nejsi hráč v této hře")
        if current_user.id != game.current_turn_user_id:
            raise HTTPException(status_code=400, detail="Nejsi na tahu")
        team1_ids = _team_ids(db, game_id, 1)
        symbol = "X" if current_user.id in team1_ids else "O"
    else:
        if current_user.id not in (game.player1_id, game.player2_id):
            raise HTTPException(status_code=403, detail="Nejsi hráč v této hře")
        if current_user.id != game.current_turn_user_id:
            raise HTTPException(status_code=400, detail="Nejsi na tahu")
        symbol = "X" if current_user.id == game.player1_id else "O"

    board = game_service.board_from_json(game.board)

    try:
        new_board = game_service.apply_move(board, payload.position, symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    game.board = game_service.board_to_json(new_board)
    result = game_service.check_winner(new_board)

    if result == "draw":
        game.status = GameStatus.FINISHED
        game.is_draw = True
        game.finished_at = datetime.now(timezone.utc)
        if is_team_game:
            _settle_pot(db, game, "draw", team1_ids + _team_ids(db, game_id, 2), [])
        else:
            _settle_pot(db, game, "draw", [game.player1_id, game.player2_id], [])
    elif result in ("X", "O"):
        game.status = GameStatus.FINISHED
        game.finished_at = datetime.now(timezone.utc)
        if is_team_game:
            team2_ids = _team_ids(db, game_id, 2)
            winner_team = 1 if result == "X" else 2
            game.winner_team = winner_team
            winners = team1_ids if winner_team == 1 else team2_ids
            _settle_pot(db, game, "win", team1_ids + team2_ids, winners)
        else:
            game.winner_user_id = game.player1_id if result == "X" else game.player2_id
            _settle_pot(db, game, "win", [game.player1_id, game.player2_id], [game.winner_user_id])
    else:
        # hra pokračuje - předej tah dalšímu hráči na řadě
        if is_team_game:
            next_idx = game_service.next_turn_index(turn_order, game.turn_index)
            game.turn_index = next_idx
            game.current_turn_user_id = turn_order[next_idx]
        else:
            game.current_turn_user_id = (
                game.player2_id if current_user.id == game.player1_id else game.player1_id
            )

    db.commit()
    db.refresh(game)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="game_move",
        actor_user_id=current_user.id,
        target=f"game:{game_id}",
        meta={"position": payload.position, "result": result},
    )
    return _game_out(db, game)


@router.get("/{game_id}", response_model=GameOut)
def read_game(
    game_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)
    if not _is_member(db, game.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro zobrazení hry musíš být členem místnosti")
    return _game_out(db, game)


@router.get("/room/{room_id}", response_model=List[GameOut])
def list_room_games(
    room_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    if not _is_member(db, room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro zobrazení her musíš být členem místnosti")
    games = db.query(Game).filter(Game.room_id == room_id).order_by(Game.created_at.desc()).all()
    return [_game_out(db, g) for g in games]


@router.post("/{game_id}/watch", status_code=204)
def watch_game(
    game_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)
    if not _is_member(db, game.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro sledování hry musíš být členem místnosti")

    existing = (
        db.query(GameSpectator)
        .filter(GameSpectator.game_id == game_id, GameSpectator.user_id == current_user.id)
        .first()
    )
    if existing:
        return  # idempotentní

    db.add(GameSpectator(game_id=game_id, user_id=current_user.id))
    db.commit()


@router.post("/{game_id}/unwatch", status_code=204)
def unwatch_game(
    game_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_game_or_404(db, game_id)
    spectator = (
        db.query(GameSpectator)
        .filter(GameSpectator.game_id == game_id, GameSpectator.user_id == current_user.id)
        .first()
    )
    if spectator:
        db.delete(spectator)
        db.commit()


@router.get("/{game_id}/spectators", response_model=List[SpectatorOut])
def list_spectators(
    game_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    game = _get_game_or_404(db, game_id)
    if not _is_member(db, game.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro seznam diváků musíš být členem místnosti")

    spectators = db.query(GameSpectator).filter(GameSpectator.game_id == game_id).all()
    return [
        SpectatorOut(user_id=s.user_id, started_watching_at=s.started_watching_at)
        for s in spectators
    ]
