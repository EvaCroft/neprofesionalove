"""
Referral systém - uživatel má vlastní referral kód, při registraci nového
uživatele s tímto kódem dostane pozvatel odměnu (viz credit_service).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean

from app.db import Base


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ReferralUse(Base):
    __tablename__ = "referral_uses"

    id = Column(Integer, primary_key=True, index=True)
    referral_code_id = Column(Integer, ForeignKey("referral_codes.id"), nullable=False, index=True)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)  # 1 kód použije uživatel max jednou (při registraci)
    used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reward_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    reward_granted = Column(Boolean, nullable=False, default=False)
