from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.auction import Auction, Bid, AuctionStatus
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.routers.rooms import _get_room_or_404, _is_member
from app.schemas import AuctionCreate, BidCreate, AuctionOut, BidOut
from app.services import credit_service

router = APIRouter(prefix="/auctions", tags=["auctions"])


def _auction_out(a: Auction) -> AuctionOut:
    return AuctionOut(
        id=a.id, room_id=a.room_id, creator_id=a.creator_id, item_description=a.item_description,
        starting_price=str(a.starting_price), current_price=str(a.current_price),
        current_bidder_id=a.current_bidder_id, status=a.status.value,
        ends_at=a.ends_at, created_at=a.created_at, closed_at=a.closed_at,
    )


def _get_auction_or_404(db: Session, auction_id: int) -> Auction:
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Aukce nenalezena")
    return auction


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _finalize_auction(db: Session, auction: Auction) -> None:
    if auction.current_bidder_id:
        credit_service.transfer(
            db, auction.current_bidder_id, auction.creator_id, Decimal(auction.current_price),
            reason=f"vydražená položka '{auction.item_description}' (aukce #{auction.id})",
        )
    auction.status = AuctionStatus.CLOSED
    auction.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(auction)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="auction_closed",
        target=f"auction:{auction.id}",
        meta={"winner": auction.current_bidder_id, "final_price": str(auction.current_price)},
    )


def _expire_if_needed(db: Session, auction: Auction) -> Auction:
    """Líná expirace - aukce se formálně uzavře při prvním přístupu po
    ends_at (žádný background scheduler v tomto MVP). Finalizuje převod
    kreditu, pokud existuje vítěz."""
    if auction.status == AuctionStatus.OPEN and datetime.now(timezone.utc) >= _aware(auction.ends_at):
        _finalize_auction(db, auction)
    return auction


@router.post("", response_model=AuctionOut, status_code=201)
def create_auction(
    payload: AuctionCreate,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, payload.room_id)
    if not _is_member(db, payload.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro založení aukce musíš být členem místnosti")
    if not payload.item_description.strip():
        raise HTTPException(status_code=400, detail="item_description nemůže být prázdný")
    if payload.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="duration_minutes musí být kladné")

    try:
        starting_price = Decimal(payload.starting_price)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="starting_price musí být platné číslo")
    if starting_price <= 0:
        raise HTTPException(status_code=400, detail="starting_price musí být kladná")

    auction = Auction(
        room_id=payload.room_id,
        creator_id=current_user.id,
        item_description=payload.item_description.strip(),
        starting_price=starting_price,
        current_price=starting_price,
        status=AuctionStatus.OPEN,
        ends_at=datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes),
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="auction_created",
        actor_user_id=current_user.id,
        target=f"room:{payload.room_id}:auction:{auction.id}",
    )
    return _auction_out(auction)


@router.post("/{auction_id}/bid", response_model=AuctionOut)
def place_bid(
    auction_id: int,
    payload: BidCreate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    auction = _get_auction_or_404(db, auction_id)
    auction = _expire_if_needed(db, auction)

    if auction.status != AuctionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Aukce už je uzavřená")
    if not _is_member(db, auction.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro příhoz musíš být členem místnosti")
    if current_user.id == auction.creator_id:
        raise HTTPException(status_code=400, detail="Nemůžeš dražit vlastní položku")

    try:
        amount = Decimal(payload.amount)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="amount musí být platné číslo")
    if amount <= Decimal(auction.current_price):
        raise HTTPException(
            status_code=400,
            detail=f"Příhoz musí být vyšší než aktuální cena ({auction.current_price})",
        )

    db.add(Bid(auction_id=auction_id, bidder_id=current_user.id, amount=amount))
    auction.current_price = amount
    auction.current_bidder_id = current_user.id
    db.commit()
    db.refresh(auction)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="auction_bid_placed",
        actor_user_id=current_user.id,
        target=f"auction:{auction_id}",
        meta={"amount": str(amount)},
    )
    return _auction_out(auction)


@router.post("/{auction_id}/close", response_model=AuctionOut)
def close_auction(
    auction_id: int,
    current_user: User = Depends(require_role(RoleEnum.CREATOR)),
    db: Session = Depends(get_db),
):
    auction = _get_auction_or_404(db, auction_id)
    if auction.creator_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Jen zakladatel aukce (nebo admin) může aukci předčasně uzavřít")
    if auction.status != AuctionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Aukce už je uzavřená")

    _finalize_auction(db, auction)
    return _auction_out(auction)


@router.get("/{auction_id}", response_model=AuctionOut)
def read_auction(
    auction_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    auction = _get_auction_or_404(db, auction_id)
    auction = _expire_if_needed(db, auction)
    if not _is_member(db, auction.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro zobrazení aukce musíš být členem místnosti")
    return _auction_out(auction)


@router.get("/{auction_id}/bids", response_model=List[BidOut])
def list_bids(
    auction_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    auction = _get_auction_or_404(db, auction_id)
    if not _is_member(db, auction.room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro zobrazení příhozů musíš být členem místnosti")

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(Bid.created_at.desc()).all()
    return [BidOut(id=b.id, bidder_id=b.bidder_id, amount=str(b.amount), created_at=b.created_at) for b in bids]


@router.get("/room/{room_id}", response_model=List[AuctionOut])
def list_room_auctions(
    room_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    if not _is_member(db, room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Pro zobrazení aukcí musíš být členem místnosti")

    auctions = db.query(Auction).filter(Auction.room_id == room_id).order_by(Auction.created_at.desc()).all()
    return [_auction_out(_expire_if_needed(db, a)) for a in auctions]
