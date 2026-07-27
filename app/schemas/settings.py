from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SettingOut(BaseModel):
    key: str
    value: Optional[str] = None

    class Config:
        from_attributes = True


class SettingUpdate(BaseModel):
    value: Optional[str] = None


class WallSettingsOut(BaseModel):
    user_id: int
    auto_post_actions: dict[str, bool] = {}


class WallSettingsUpdate(BaseModel):
    actions: dict[str, bool]


class ActivitySettingsOut(BaseModel):
    user_id: int
    visible_actions: dict[str, bool] = {}


class ActivitySettingsUpdate(BaseModel):
    actions: dict[str, bool]


class ActivityEntryOut(BaseModel):
    action: str
    timestamp: datetime
    text: str
