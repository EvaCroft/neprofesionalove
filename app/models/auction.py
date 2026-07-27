"""
Model Auction + Bid - živé aukce vázané na místnost (dle konceptu: "pouze
v místnostech"). Uzavření aukce převede kredit od vítěze zakladateli přes
credit_service.transfer() - jediné legitimní místo měnící Wallet.balance.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, Text

from app.db import Base


class AuctionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_description = Column(Text, nullable=False)
    starting_price = Column(Numeric(precision=18, scale=2), nullable=False)
    current_price = Column(Numeric(precision=18, scale=2), nullable=False)
    current_bidder_id = Column(Integer, nullable=True)
    status = Column(Enum(AuctionStatus), nullable=False, default=AuctionStatus.OPEN, index=True)
    ends_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
