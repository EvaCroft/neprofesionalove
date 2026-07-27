"""
Model Wallet + Transaction (kreditový ledger).

Wallet.balance je "cache" hodnota, autoritativní zdroj pravdy je ale součet
Transaction záznamů - balance se aktualizuje výhradně přes credit_service.py,
nikde jinde v kódu se do Wallet.balance nesmí zapisovat přímo (viz v12 audit).
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, Text

from app.db import Base


class TransactionType(str, enum.Enum):
    TOPUP = "topup"
    WITHDRAWAL = "withdrawal"
    WITHDRAWAL_REVERSAL = "withdrawal_reversal"  # refund při zamítnutí žádosti o výplatu
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    REWARD = "reward"
    ROOM_FEE_IN = "room_fee_in"   # příjem poplatku (vlastník místnosti)
    ROOM_FEE_OUT = "room_fee_out"  # platba poplatku (vstupující uživatel)
    GAME_STAKE_OUT = "game_stake_out"      # vklad do hry při založení/připojení (v16)
    GAME_STAKE_IN = "game_stake_in"        # výhra potu při vítězství (v16)
    GAME_STAKE_REFUND = "game_stake_refund"  # vrácení vkladu při remíze (v16)


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance = Column(Numeric(precision=18, scale=2), nullable=False, default=0)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)  # vždy kladné číslo
    related_user_id = Column(Integer, nullable=True)  # druhá strana u transferu/room fee
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
