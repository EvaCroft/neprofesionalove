import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.referral import ReferralCode, ReferralUse
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import ReferralCodeOut, ReferralUseOut

router = APIRouter(prefix="/referral", tags=["referral"])


def _generate_unique_code(db: Session) -> str:
    for _ in range(10):
        candidate = secrets.token_hex(4).upper()  # 8 znaků, např. "A1B2C3D4"
        if not db.query(ReferralCode).filter(ReferralCode.code == candidate).first():
            return candidate
    raise RuntimeError("Nepodařilo se vygenerovat unikátní referral kód")


@router.get("/my-code", response_model=ReferralCodeOut)
def get_or_create_my_code(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    referral = db.query(ReferralCode).filter(ReferralCode.owner_user_id == current_user.id).first()
    if not referral:
        referral = ReferralCode(owner_user_id=current_user.id, code=_generate_unique_code(db))
        db.add(referral)
        db.commit()
        db.refresh(referral)
    return referral


@router.get("/uses", response_model=list[ReferralUseOut])
def list_my_referral_uses(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    referral = db.query(ReferralCode).filter(ReferralCode.owner_user_id == current_user.id).first()
    if not referral:
        return []
    uses = db.query(ReferralUse).filter(ReferralUse.referral_code_id == referral.id).all()
    return [
        ReferralUseOut(
            used_by_user_id=u.used_by_user_id, used_at=u.used_at,
            reward_amount=str(u.reward_amount), reward_granted=u.reward_granted,
        )
        for u in uses
    ]
