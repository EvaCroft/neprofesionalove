from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WalletTopup(BaseModel):
    amount: str
    reason: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: str
    related_user_id: Optional[int] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WalletOut(BaseModel):
    user_id: int
    balance: str
    transactions: List[TransactionOut] = []


class TransferCreate(BaseModel):
    to_user_id: int
    amount: str  # string kvůli přesnosti Decimal přes JSON
    reason: Optional[str] = None


class WithdrawalRequestCreate(BaseModel):
    amount: str
    note: Optional[str] = None


class WithdrawalRequestOut(BaseModel):
    id: int
    user_id: int
    amount: str
    status: str
    note: Optional[str] = None
    requested_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None

    class Config:
        from_attributes = True
