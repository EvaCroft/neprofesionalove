from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.referral import ReferralCode, ReferralUse
from app.models.settings import AppSetting
from app.models.user import User
from app.models.wallet import TransactionType
from app.schemas import UserRegister, UserLogin, UserOut, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

DEFAULT_REFERRAL_REWARD = Decimal("10.00")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Neplatné nebo vypršelé přihlášení",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="register_failed_duplicate_email",
            target=payload.email,
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="E-mail už je registrovaný")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="user_registered",
        actor_user_id=user.id,
        target=user.email,
        ip_address=request.client.host if request.client else None,
    )

    if payload.referral_code:
        _process_referral_code(db, payload.referral_code, user)

    return user


def _process_referral_code(db: Session, code: str, new_user: User) -> None:
    """Pokud je kód platný, udělí pozvateli odměnu. Neplatný kód registraci
    NEblokuje - jen se tiše zaloguje jako chyba (uživatel to nemusí vidět
    jako fatal error, jen o odměnu pozvatel nepřijde)."""
    from app.services import credit_service

    referral = db.query(ReferralCode).filter(ReferralCode.code == code.strip().upper()).first()
    if not referral:
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="referral_code_invalid",
            actor_user_id=new_user.id,
            target=code,
        )
        return

    setting = db.query(AppSetting).filter(AppSetting.key == "referral_reward_amount").first()
    reward_amount = Decimal(setting.value) if setting and setting.value else DEFAULT_REFERRAL_REWARD

    use = ReferralUse(
        referral_code_id=referral.id,
        used_by_user_id=new_user.id,
        reward_amount=reward_amount,
        reward_granted=True,
    )
    db.add(use)
    db.commit()

    credit_service.deposit(
        db, referral.owner_user_id, reward_amount, TransactionType.REWARD,
        related_user_id=new_user.id,
        reason=f"referral odměna za pozvání uživatele #{new_user.id}",
        actor_user_id=new_user.id,
    )

    # samostatný log záznam pro Aktivitu pozvatele (credit_service.deposit
    # výše loguje jen obecný wallet_deposit_reward s actor=nový uživatel;
    # tohle je explicitně přiřazené k pozvateli, stejný vzor jako u ostatních
    # akcí v ACTIVITY_ACTION_KEYS - viz app/services/activity_service.py)
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="referral_reward_earned",
        actor_user_id=referral.owner_user_id,
        target=f"user:{new_user.id}",
        meta={"amount": str(reward_amount), "invited_user_id": new_user.id},
    )


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    ip = request.client.host if request.client else None

    if not user or not verify_password(payload.password, user.password_hash):
        log_event(
            db, LogType.OPERATION_USER_LOG_ERROR,
            action="login_failed",
            target=payload.email,
            ip_address=ip,
        )
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="user_login",
        actor_user_id=user.id,
        target=user.email,
        ip_address=ip,
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
