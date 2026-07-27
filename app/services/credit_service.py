"""
Credit service - jediné legitimní místo v kódu, které smí měnit
Wallet.balance. Všechny endpointy pracující s kreditem MUSÍ volat tyto
funkce, nikdy nezapisovat do Wallet.balance přímo (viz v12 audit).

Každá operace zapíše i Transaction záznam (immutable ledger) a systémový
log (operation_user_log).
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.logging_service import log_event
from app.models.log import LogType
from app.models.wallet import Wallet, Transaction, TransactionType


class InsufficientFundsError(Exception):
    pass


def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=Decimal("0"))
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def _record_transaction(
    db: Session,
    wallet: Wallet,
    tx_type: TransactionType,
    amount: Decimal,
    related_user_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> Transaction:
    tx = Transaction(
        wallet_id=wallet.id,
        type=tx_type,
        amount=amount,
        related_user_id=related_user_id,
        reason=reason,
    )
    db.add(tx)
    return tx


def deposit(
    db: Session,
    user_id: int,
    amount: Decimal,
    tx_type: TransactionType,
    related_user_id: Optional[int] = None,
    reason: Optional[str] = None,
    actor_user_id: Optional[int] = None,
) -> Wallet:
    if amount <= 0:
        raise ValueError("Částka musí být kladná")

    wallet = get_or_create_wallet(db, user_id)
    wallet.balance = Decimal(wallet.balance) + amount
    _record_transaction(db, wallet, tx_type, amount, related_user_id, reason)
    db.commit()
    db.refresh(wallet)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action=f"wallet_deposit_{tx_type.value}",
        actor_user_id=actor_user_id or user_id,
        target=f"user:{user_id}",
        meta={"amount": str(amount), "new_balance": str(wallet.balance)},
    )
    return wallet


def withdraw(
    db: Session,
    user_id: int,
    amount: Decimal,
    tx_type: TransactionType,
    related_user_id: Optional[int] = None,
    reason: Optional[str] = None,
    actor_user_id: Optional[int] = None,
) -> Wallet:
    if amount <= 0:
        raise ValueError("Částka musí být kladná")

    wallet = get_or_create_wallet(db, user_id)
    if Decimal(wallet.balance) < amount:
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action=f"wallet_withdraw_failed_insufficient_funds_{tx_type.value}",
            actor_user_id=actor_user_id or user_id,
            target=f"user:{user_id}",
            meta={"amount": str(amount), "balance": str(wallet.balance)},
        )
        raise InsufficientFundsError(
            f"Nedostatečný zůstatek: {wallet.balance} < {amount}"
        )

    wallet.balance = Decimal(wallet.balance) - amount
    _record_transaction(db, wallet, tx_type, amount, related_user_id, reason)
    db.commit()
    db.refresh(wallet)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action=f"wallet_withdraw_{tx_type.value}",
        actor_user_id=actor_user_id or user_id,
        target=f"user:{user_id}",
        meta={"amount": str(amount), "new_balance": str(wallet.balance)},
    )
    return wallet


def transfer(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    amount: Decimal,
    reason: Optional[str] = None,
) -> None:
    if from_user_id == to_user_id:
        raise ValueError("Nelze převést kredit sám sobě")

    withdraw(
        db, from_user_id, amount, TransactionType.TRANSFER_OUT,
        related_user_id=to_user_id, reason=reason, actor_user_id=from_user_id,
    )
    deposit(
        db, to_user_id, amount, TransactionType.TRANSFER_IN,
        related_user_id=from_user_id, reason=reason, actor_user_id=from_user_id,
    )


def charge_room_fee(
    db: Session,
    payer_user_id: int,
    owner_user_id: int,
    amount: Decimal,
    room_id: int,
) -> None:
    """Strhne poplatek za vstup do placené místnosti od uživatele a připíše
    ho vlastníkovi místnosti. Vyhazuje InsufficientFundsError, pokud
    uživatel nemá dost prostředků (join se pak zamítne)."""
    reason = f"vstupné do místnosti #{room_id}"
    withdraw(
        db, payer_user_id, amount, TransactionType.ROOM_FEE_OUT,
        related_user_id=owner_user_id, reason=reason, actor_user_id=payer_user_id,
    )
    deposit(
        db, owner_user_id, amount, TransactionType.ROOM_FEE_IN,
        related_user_id=payer_user_id, reason=reason, actor_user_id=payer_user_id,
    )
