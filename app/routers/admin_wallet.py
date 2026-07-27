from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.user import User, RoleEnum
from app.models.wallet import TransactionType, Transaction
from app.models.withdrawal import WithdrawalRequest, WithdrawalStatus
from app.permissions import require_role
from app.schemas import WalletTopup, WalletOut, TransactionOut, WithdrawalRequestOut
from app.services import credit_service

router = APIRouter(prefix="/admin", tags=["admin-wallet"])


def _withdrawal_out(r: WithdrawalRequest) -> WithdrawalRequestOut:
    return WithdrawalRequestOut(
        id=r.id, user_id=r.user_id, amount=str(r.amount), status=r.status.value,
        note=r.note, requested_at=r.requested_at, resolved_at=r.resolved_at,
        resolved_by=r.resolved_by,
    )


@router.post("/wallet/{user_id}/topup", response_model=WalletOut)
def admin_topup_wallet(
    user_id: int,
    payload: WalletTopup,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    """v8 placeholder - žádná reálná platební brána zatím není napojena.
    Admin ručně připíše kredit (např. po přijetí platby mimo systém).
    Reálná integrace platebního providera je otevřený bod v backlogu."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    try:
        amount = Decimal(payload.amount)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="amount musí být platné číslo")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount musí být kladné")

    wallet = credit_service.deposit(
        db, user_id, amount, TransactionType.TOPUP,
        reason=payload.reason or "admin topup",
        actor_user_id=current_user.id,
    )

    transactions = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return WalletOut(
        user_id=user_id,
        balance=str(wallet.balance),
        transactions=[
            TransactionOut(
                id=t.id, type=t.type.value, amount=str(t.amount),
                related_user_id=t.related_user_id, reason=t.reason, created_at=t.created_at,
            )
            for t in transactions
        ],
    )


@router.post("/wallet/{user_id}/reward", response_model=WalletOut)
def admin_reward_wallet(
    user_id: int,
    payload: WalletTopup,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    """Obecné udělení odměny adminem - za testování/bug report/streamování/
    zvaní členů/atd. (dokud nejsou navázané automatické triggery pro
    jednotlivé druhy odměn - viz backlog)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="reason je u odměny povinný (důvod udělení)")

    try:
        amount = Decimal(payload.amount)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="amount musí být platné číslo")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount musí být kladné")

    wallet = credit_service.deposit(
        db, user_id, amount, TransactionType.REWARD,
        reason=payload.reason, actor_user_id=current_user.id,
    )

    transactions = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return WalletOut(
        user_id=user_id,
        balance=str(wallet.balance),
        transactions=[
            TransactionOut(
                id=t.id, type=t.type.value, amount=str(t.amount),
                related_user_id=t.related_user_id, reason=t.reason, created_at=t.created_at,
            )
            for t in transactions
        ],
    )


@router.get("/withdraw-requests", response_model=List[WithdrawalRequestOut])
def list_withdrawal_requests(
    status: Optional[str] = None,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(WithdrawalRequest)
    if status:
        try:
            query = query.filter(WithdrawalRequest.status == WithdrawalStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Neplatný status")
    requests = query.order_by(WithdrawalRequest.requested_at.desc()).all()
    return [_withdrawal_out(r) for r in requests]


@router.put("/withdraw-requests/{request_id}/approve", response_model=WithdrawalRequestOut)
def approve_withdrawal(
    request_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    wr = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail="Žádost nenalezena")
    if wr.status != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Žádost už má stav '{wr.status.value}', nelze schválit")

    wr.status = WithdrawalStatus.APPROVED
    wr.resolved_at = datetime.now(timezone.utc)
    wr.resolved_by = current_user.id
    db.commit()
    db.refresh(wr)

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="withdrawal_approved",
        actor_user_id=current_user.id,
        target=f"withdrawal:{request_id}",
        ip_address=request.client.host if request.client else None,
    )
    return _withdrawal_out(wr)


@router.put("/withdraw-requests/{request_id}/reject", response_model=WithdrawalRequestOut)
def reject_withdrawal(
    request_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    wr = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail="Žádost nenalezena")
    if wr.status != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Žádost už má stav '{wr.status.value}', nelze zamítnout")

    # refund - vrátit strženou částku zpět na peněženku
    credit_service.deposit(
        db, wr.user_id, wr.amount, TransactionType.WITHDRAWAL_REVERSAL,
        reason=f"zamítnutá žádost o výplatu #{wr.id}",
        actor_user_id=current_user.id,
    )

    wr.status = WithdrawalStatus.REJECTED
    wr.resolved_at = datetime.now(timezone.utc)
    wr.resolved_by = current_user.id
    db.commit()
    db.refresh(wr)

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="withdrawal_rejected",
        actor_user_id=current_user.id,
        target=f"withdrawal:{request_id}",
        ip_address=request.client.host if request.client else None,
    )
    return _withdrawal_out(wr)


@router.put("/withdraw-requests/{request_id}/mark-paid", response_model=WithdrawalRequestOut)
def mark_withdrawal_paid(
    request_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    wr = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail="Žádost nenalezena")
    if wr.status != WithdrawalStatus.APPROVED:
        raise HTTPException(status_code=400, detail=f"Žádost musí být 'approved' (je '{wr.status.value}')")

    wr.status = WithdrawalStatus.PAID
    db.commit()
    db.refresh(wr)

    log_event(
        db, LogType.OPERATION_SYSTEM_LOG,
        action="withdrawal_marked_paid",
        actor_user_id=current_user.id,
        target=f"withdrawal:{request_id}",
        ip_address=request.client.host if request.client else None,
    )
    return _withdrawal_out(wr)
