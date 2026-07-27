# --- v24: Vztahy (přátelství + sledování) ---

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FriendUserSummary(BaseModel):
    """Lehký souhrn uživatele pro seznamy (přátelé/žádosti/sledující) -
    vyhne se tomu, aby si frontend musel dotahovat profil zvlášť pro
    každou položku seznamu."""
    user_id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class FriendRequestOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str  # "pending" | "accepted"
    created_at: datetime
    user: FriendUserSummary  # druhá strana vztahu (ne já)


class FriendRelationOut(BaseModel):
    """Stav vztahu aktuálně přihlášeného uživatele vůči `user_id` z URL."""
    friend_status: str  # "none" | "pending_sent" | "pending_received" | "friends"
    is_following: bool
    is_followed_by: bool


class FriendCountsOut(BaseModel):
    friends_count: int
    followers_count: int
    following_count: int
