"""
Router Vztahy - přátelství (žádost/přijetí) + sledování (v24, viz DEVLOG #044).

Dva nezávislé systémy v jednom routeru, protože spolu úzce sdílí kontext
(cizí profil, tlačítka vedle sebe), ale mají odlišnou logiku:
- Přátelství (`FriendRequest`) - vzájemné, vyžaduje odeslání + přijetí.
- Sledování (`Follow`) - jednosměrné, okamžité, bez schvalování.

Seznamy přátel/sledujících/sledovaných jsou guest-friendly (bez auth) -
stejný vzor jako Zeď/Aktivita/Události ("veřejný" pohled na cizí profil).
Akce (odeslat žádost, přijmout, sledovat...) vyžadují přihlášení.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.follow import Follow
from app.models.friendship import FriendRequest, FriendRequestStatus
from app.models.log import LogType
from app.models.profile import Profile
from app.models.user import RoleEnum, User
from app.permissions import require_role
from app.schemas import (
    FriendCountsOut, FriendRelationOut, FriendRequestOut, FriendUserSummary,
)

router = APIRouter(prefix="/friends", tags=["friends"])


def _user_summary(db: Session, user_id: int) -> FriendUserSummary:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    return FriendUserSummary(
        user_id=user_id,
        display_name=(profile.display_name if profile else None),
        avatar_url=(profile.avatar_url if profile else None),
    )


def _existing_relation(db: Session, user_a: int, user_b: int) -> Optional[FriendRequest]:
    return db.query(FriendRequest).filter(
        or_(
            (FriendRequest.from_user_id == user_a) & (FriendRequest.to_user_id == user_b),
            (FriendRequest.from_user_id == user_b) & (FriendRequest.to_user_id == user_a),
        )
    ).first()


def _friend_ids(db: Session, user_id: int) -> List[int]:
    rows = db.query(FriendRequest).filter(
        FriendRequest.status == FriendRequestStatus.ACCEPTED,
        or_(FriendRequest.from_user_id == user_id, FriendRequest.to_user_id == user_id),
    ).all()
    return [r.to_user_id if r.from_user_id == user_id else r.from_user_id for r in rows]


def _log(db: Session, request: Request, actor_id: int, action: str, target_user_id: int):
    log_event(
        db, LogType.OPERATION_USER_LOG,
        action=action,
        actor_user_id=actor_id,
        target=str(target_user_id),
        ip_address=request.client.host if request.client else None,
        meta={"target_user_id": target_user_id},
    )


# --- Přátelství: žádosti ---

@router.post("/request/{user_id}", response_model=FriendRequestOut, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Nelze poslat žádost sám sobě")
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    existing = _existing_relation(db, current_user.id, user_id)
    if existing:
        if existing.status == FriendRequestStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Už jste přátelé")
        raise HTTPException(status_code=400, detail="Žádost už existuje (čeká na vyřízení)")

    fr = FriendRequest(from_user_id=current_user.id, to_user_id=user_id, status=FriendRequestStatus.PENDING)
    db.add(fr)
    db.commit()
    db.refresh(fr)

    _log(db, request, current_user.id, "friend_request_sent", user_id)

    return FriendRequestOut(
        id=fr.id, from_user_id=fr.from_user_id, to_user_id=fr.to_user_id,
        status=fr.status.value, created_at=fr.created_at,
        user=_user_summary(db, user_id),
    )


@router.post("/accept/{user_id}", response_model=FriendRequestOut)
def accept_friend_request(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """`user_id` = kdo žádost poslal (žádost musí směřovat na mě)."""
    fr = db.query(FriendRequest).filter(
        FriendRequest.from_user_id == user_id,
        FriendRequest.to_user_id == current_user.id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).first()
    if not fr:
        raise HTTPException(status_code=404, detail="Žádost o přátelství nenalezena")

    fr.status = FriendRequestStatus.ACCEPTED
    db.commit()
    db.refresh(fr)

    _log(db, request, current_user.id, "friend_request_accepted", user_id)

    return FriendRequestOut(
        id=fr.id, from_user_id=fr.from_user_id, to_user_id=fr.to_user_id,
        status=fr.status.value, created_at=fr.created_at,
        user=_user_summary(db, user_id),
    )


@router.delete("/decline/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def decline_friend_request(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Odmítnutí příchozí žádosti (`user_id` = odesílatel)."""
    fr = db.query(FriendRequest).filter(
        FriendRequest.from_user_id == user_id,
        FriendRequest.to_user_id == current_user.id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).first()
    if not fr:
        raise HTTPException(status_code=404, detail="Žádost o přátelství nenalezena")
    db.delete(fr)
    db.commit()
    _log(db, request, current_user.id, "friend_request_declined", user_id)
    return None


@router.delete("/cancel/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_friend_request(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Zrušení vlastní odeslané žádosti (`user_id` = příjemce)."""
    fr = db.query(FriendRequest).filter(
        FriendRequest.from_user_id == current_user.id,
        FriendRequest.to_user_id == user_id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).first()
    if not fr:
        raise HTTPException(status_code=404, detail="Žádost o přátelství nenalezena")
    db.delete(fr)
    db.commit()
    _log(db, request, current_user.id, "friend_request_cancelled", user_id)
    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfriend(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    fr = db.query(FriendRequest).filter(
        FriendRequest.status == FriendRequestStatus.ACCEPTED,
        or_(
            (FriendRequest.from_user_id == current_user.id) & (FriendRequest.to_user_id == user_id),
            (FriendRequest.from_user_id == user_id) & (FriendRequest.to_user_id == current_user.id),
        ),
    ).first()
    if not fr:
        raise HTTPException(status_code=404, detail="Přátelství nenalezeno")
    db.delete(fr)
    db.commit()
    _log(db, request, current_user.id, "friend_removed", user_id)
    return None


@router.get("/requests/incoming", response_model=List[FriendRequestOut])
def list_incoming_requests(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    rows = db.query(FriendRequest).filter(
        FriendRequest.to_user_id == current_user.id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).order_by(FriendRequest.created_at.desc()).all()
    return [
        FriendRequestOut(
            id=r.id, from_user_id=r.from_user_id, to_user_id=r.to_user_id,
            status=r.status.value, created_at=r.created_at,
            user=_user_summary(db, r.from_user_id),
        ) for r in rows
    ]


@router.get("/requests/sent", response_model=List[FriendRequestOut])
def list_sent_requests(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    rows = db.query(FriendRequest).filter(
        FriendRequest.from_user_id == current_user.id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).order_by(FriendRequest.created_at.desc()).all()
    return [
        FriendRequestOut(
            id=r.id, from_user_id=r.from_user_id, to_user_id=r.to_user_id,
            status=r.status.value, created_at=r.created_at,
            user=_user_summary(db, r.to_user_id),
        ) for r in rows
    ]


@router.get("/list/{user_id}", response_model=List[FriendUserSummary])
def list_friends(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Veřejný seznam přátel daného uživatele (guest-friendly, stejně jako Zeď/Aktivita)."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    ids = _friend_ids(db, user_id)[skip: skip + min(limit, 200)]
    return [_user_summary(db, fid) for fid in ids]


# --- Sledování ---

@router.post("/follow/{user_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Nelze sledovat sám sebe")
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id, Follow.followed_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Už sledujete")

    db.add(Follow(follower_id=current_user.id, followed_id=user_id))
    db.commit()
    _log(db, request, current_user.id, "user_followed", user_id)
    return {"following": True}


@router.delete("/follow/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id, Follow.followed_id == user_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Sledování nenalezeno")
    db.delete(existing)
    db.commit()
    _log(db, request, current_user.id, "user_unfollowed", user_id)
    return None


@router.get("/followers/{user_id}", response_model=List[FriendUserSummary])
def list_followers(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Kdo sleduje `user_id` (guest-friendly)."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    rows = db.query(Follow).filter(Follow.followed_id == user_id) \
        .offset(skip).limit(min(limit, 200)).all()
    return [_user_summary(db, r.follower_id) for r in rows]


@router.get("/following/{user_id}", response_model=List[FriendUserSummary])
def list_following(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Koho sleduje `user_id` (guest-friendly)."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    rows = db.query(Follow).filter(Follow.follower_id == user_id) \
        .offset(skip).limit(min(limit, 200)).all()
    return [_user_summary(db, r.followed_id) for r in rows]


# --- Souhrnné endpointy pro profil ---

@router.get("/counts/{user_id}", response_model=FriendCountsOut)
def get_counts(user_id: int, db: Session = Depends(get_db)):
    """Guest-friendly čítače pro sekci 'O mně' (v27 je použije, ale dává smysl
    je mít hotové hned s backendem)."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    friends_count = len(_friend_ids(db, user_id))
    followers_count = db.query(Follow).filter(Follow.followed_id == user_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user_id).count()
    return FriendCountsOut(
        friends_count=friends_count, followers_count=followers_count, following_count=following_count,
    )


@router.get("/status/{user_id}", response_model=FriendRelationOut)
def get_relation_status(
    user_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Vztah přihlášeného uživatele k `user_id` - pohání tlačítka na cizím profilu."""
    friend_status = "none"
    if user_id != current_user.id:
        fr = _existing_relation(db, current_user.id, user_id)
        if fr:
            if fr.status == FriendRequestStatus.ACCEPTED:
                friend_status = "friends"
            elif fr.from_user_id == current_user.id:
                friend_status = "pending_sent"
            else:
                friend_status = "pending_received"

    is_following = db.query(Follow).filter(
        Follow.follower_id == current_user.id, Follow.followed_id == user_id
    ).first() is not None
    is_followed_by = db.query(Follow).filter(
        Follow.follower_id == user_id, Follow.followed_id == current_user.id
    ).first() is not None

    return FriendRelationOut(
        friend_status=friend_status, is_following=is_following, is_followed_by=is_followed_by,
    )
