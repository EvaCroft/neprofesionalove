"""
Model WithdrawalRequest - žádost o výplatu kreditu.

Flow: pending -> approved -> paid, nebo pending -> rejected (s refundem).
Částka se strhává z peněženky HNED při vytvoření žádosti (escrow), aby ji
uživatel nemohl mezitím utratit; při zamítnutí se vrací zpět.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Numeric, Text

from app.db import Base


class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    status = Column(Enum(WithdrawalStatus), nullable=False, default=WithdrawalStatus.PENDING, index=True)
    note = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)  # admin user_id
