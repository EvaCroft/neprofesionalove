from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuctionCreate(BaseModel):
    room_id: int
    item_description: str
    starting_price: str
    duration_minutes: int = 60


class BidCreate(BaseModel):
    amount: str


class AuctionOut(BaseModel):
    id: int
    room_id: int
    creator_id: int
    item_description: str
    starting_price: str
    current_price: str
    current_bidder_id: Optional[int] = None
    status: str
    ends_at: datetime
    created_at: datetime
    closed_at: Optional[datetime] = None


class BidOut(BaseModel):
    id: int
    bidder_id: int
    amount: str
    created_at: datetime
