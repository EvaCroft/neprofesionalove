# --- v26: Přítomnost + čítače ---

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PresenceOut(BaseModel):
    is_online: bool
    last_active_at: Optional[datetime] = None
    activity: Optional[str] = None  # "playing" | "chatting" | None
    activity_detail: Optional[str] = None  # např. název místnosti
