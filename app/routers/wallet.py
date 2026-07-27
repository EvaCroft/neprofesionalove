from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.wallet import Transaction, TransactionType
from app.models.withdrawal import WithdrawalRequest, WithdrawalStatus
from app.models.settings import AppSetting
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import WalletOut, TransferCreate, TransactionOut, WithdrawalRequestCreate, WithdrawalRequestOut
from app.services import credit_service
from app.services.credit_service import InsufficientFundsError

router = APIRouter(prefix="/wallet", tags=["wallet"])


def _real_money_conversion_enabled(db: Session) -> bool:
    """Feature flag mitigující regulatorní riziko (viz DEVLOG backlog):
    výplata kreditu za reálné peníze je defaultně VYPNUTÁ, dokud admin
    explicitně nenastaví AppSetting['real_money_conversion_enabled']='true'."""
    setting = db.query(AppSetting).filter(AppSetting.key == "real_money_conversion_enabled").first()
    return bool(setting and setting.value == "true")


def _parse_amount(raw: str) -> Decimal:
    try:
        amount = Decimal(raw)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="amount musí být platné číslo")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount musí být kladné")
    return amount


@router.get("/me", response_model=WalletOut)
def read_my_wallet(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    wallet = credit_service.get_or_create_wallet(db, current_user.id)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return WalletOut(
        user_id=current_user.id,
        balance=str(wallet.balance),
        transactions=[
            TransactionOut(
                id=t.id, type=t.type.value, amount=str(t.amount),
                related_user_id=t.related_user_id, reason=t.reason, created_at=t.created_at,
            )
            for t in transactions
        ],
    )


@router.post("/transfer", status_code=204)
def transfer_credit(
    payload: TransferCreate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    amount = _parse_amount(payload.amount)

    recipient = db.query(User).filter(User.id == payload.to_user_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Příjemce nenalezen")

    try:
        credit_service.transfer(
            db, current_user.id, payload.to_user_id, amount, reason=payload.reason
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/withdraw-request", response_model=WithdrawalRequestOut, status_code=201)
def request_withdrawal(
    payload: WithdrawalRequestCreate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    if not _real_money_conversion_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Výplata kreditu za reálné peníze je aktuálně vypnutá (regulatorní pojistka)",
        )

    amount = _parse_amount(payload.amount)

    # Escrow: částka se strhává hned, aby ji uživatel nemohl mezitím utratit
    try:
        credit_service.withdraw(
            db, current_user.id, amount, TransactionType.WITHDRAWAL,
            reason=payload.note or "výplata - žádost",
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))

    request = WithdrawalRequest(user_id=current_user.id, amount=amount, note=payload.note)
    db.add(request)
    db.commit()
    db.refresh(request)
    return _withdrawal_out(request)


def _withdrawal_out(r: WithdrawalRequest) -> WithdrawalRequestOut:
    return WithdrawalRequestOut(
        id=r.id, user_id=r.user_id, amount=str(r.amount), status=r.status.value,
        note=r.note, requested_at=r.requested_at, resolved_at=r.resolved_at,
        resolved_by=r.resolved_by,
    )


@router.get("/withdraw-requests", response_model=list[WithdrawalRequestOut])
def list_my_withdrawal_requests(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(WithdrawalRequest)
        .filter(WithdrawalRequest.user_id == current_user.id)
        .order_by(WithdrawalRequest.requested_at.desc())
        .all()
    )
    return [_withdrawal_out(r) for r in requests]
