from datetime import datetime

from pydantic import BaseModel


class ReferralCodeOut(BaseModel):
    code: str
    owner_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralUseOut(BaseModel):
    used_by_user_id: int
    used_at: datetime
    reward_amount: str
    reward_granted: bool
