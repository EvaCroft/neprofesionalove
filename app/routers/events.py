"""
Router Události - viz PROJECT.md a BUILDPLAN.md (dokončení profilu, část 4/4).

Účast (`EventParticipation`) má 3 stavy: going/interested/went - jeden řádek
na dvojici (event, uživatel), upsert při změně stavu (ne historie). Cover
obrázek jde přes modul Média (`POST /media/upload` se `source=event_cover`),
ne přímé pole v `EventCreate`/`EventUpdate` - stejný vzor jako u profilu.

Logování: bez vlastního log typu (žádost neobsahovala rozšíření o nový
log typ) - reálné akce se logují přes `OPERATION_USER_LOG`, stejný vzor jako
`app/routers/games.py`/`app/routers/auctions.py`.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.event import Event, EventParticipation, ParticipationStatus
from app.models.log import LogType
from app.models.user import RoleEnum, User
from app.permissions import require_role
from app.schemas import EventCreate, EventOut, EventUpdate, ParticipationIn, ParticipationOut

router = APIRouter(prefix="/events", tags=["events"])


def _get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Událost nenalezena")
    return event


def _to_out(db: Session, event: Event, current_user: Optional[User]) -> EventOut:
    going = db.query(EventParticipation).filter(
        EventParticipation.event_id == event.id,
        EventParticipation.status == ParticipationStatus.GOING,
    ).count()
    interested = db.query(EventParticipation).filter(
        EventParticipation.event_id == event.id,
        EventParticipation.status == ParticipationStatus.INTERESTED,
    ).count()
    my_status = None
    if current_user:
        participation = db.query(EventParticipation).filter(
            EventParticipation.event_id == event.id,
            EventParticipation.user_id == current_user.id,
        ).first()
        if participation:
            my_status = participation.status.value
    return EventOut(
        id=event.id,
        owner_id=event.owner_id,
        title=event.title,
        description=event.description,
        starts_at=event.starts_at,
        location=event.location,
        cover_url=event.cover_url,
        created_at=event.created_at,
        going_count=going,
        interested_count=interested,
        my_status=my_status,
    )


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    event = Event(
        owner_id=current_user.id,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        location=payload.location,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="event_created",
        actor_user_id=current_user.id,
        target=str(event.id),
        ip_address=request.client.host if request.client else None,
        meta={"title": event.title, "starts_at": event.starts_at.isoformat()},
    )

    return _to_out(db, event, current_user)


@router.get("", response_model=List[EventOut])
def list_events(
    mine: bool = False,
    participating: bool = False,
    upcoming_only: bool = True,
    skip: int = 0,
    limit: int = 48,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """`mine=true` a `participating=true` se kombinují jako OR (moje akce ∪
    akce, kde mám účast) - přesně to profil potřebuje pro sekci "Moje
    události". Bez obou flagů vrací všechny (budoucí "objevit", zatím bez UI)."""
    query = db.query(Event)

    if mine or participating:
        from sqlalchemy import or_

        conditions = []
        if mine:
            conditions.append(Event.owner_id == current_user.id)
        if participating:
            participating_ids = [
                row.event_id for row in db.query(EventParticipation.event_id)
                .filter(EventParticipation.user_id == current_user.id).all()
            ]
            conditions.append(Event.id.in_(participating_ids or [-1]))
        query = query.filter(or_(*conditions))

    if upcoming_only:
        query = query.filter(Event.starts_at >= datetime.now(timezone.utc))

    query = query.order_by(Event.starts_at.asc())
    events = query.offset(skip).limit(min(limit, 200)).all()
    return [_to_out(db, e, current_user) for e in events]


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(db, event_id)
    return _to_out(db, event, current_user)


@router.put("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(db, event_id)
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Jen zakladatel může upravit událost")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return _to_out(db, event, current_user)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(db, event_id)
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Jen zakladatel může smazat událost")

    db.query(EventParticipation).filter(EventParticipation.event_id == event_id).delete()
    db.delete(event)
    db.commit()
    return None


@router.post("/{event_id}/participate", response_model=ParticipationOut)
def set_participation(
    event_id: int,
    payload: ParticipationIn,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    _get_event_or_404(db, event_id)
    try:
        status_enum = ParticipationStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Neznámý status: {payload.status}")

    participation = db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id,
        EventParticipation.user_id == current_user.id,
    ).first()
    if participation:
        participation.status = status_enum
    else:
        participation = EventParticipation(
            event_id=event_id, user_id=current_user.id, status=status_enum
        )
        db.add(participation)
    db.commit()
    db.refresh(participation)

    return ParticipationOut(
        event_id=participation.event_id,
        user_id=participation.user_id,
        status=participation.status.value,
        created_at=participation.created_at,
    )


@router.delete("/{event_id}/participate", status_code=status.HTTP_204_NO_CONTENT)
def remove_participation(
    event_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    db.query(EventParticipation).filter(
        EventParticipation.event_id == event_id,
        EventParticipation.user_id == current_user.id,
    ).delete()
    db.commit()
    return None
