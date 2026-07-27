from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.profile import Profile, VISIBILITY_CONTROLLED_FIELDS, ALWAYS_PRIVATE_FIELDS
from app.models.profile_location import ProfileLocation
from app.models.user import User
from app.permissions import require_role
from app.models.user import RoleEnum
from app.routers.posts import get_current_user_optional
from app.schemas import (
    ProfileOut, ProfileUpdate, ProfileSensitiveUpdate,
    ProfileLocationOut, ProfileLocationCreate, ProfileLocationUpdate,
    ProfileVisibilityUpdate, PresenceOut,
    GENDER_CHOICES, ORIENTATION_CHOICES, RELATIONSHIP_STATUS_CHOICES,
    SEEKING_CHOICES, VISIBILITY_LEVELS, EDUCATION_CHOICES, RELIGION_CHOICES,
)
from app.services import presence_service

router = APIRouter(prefix="/profile", tags=["profile"])

CHOICE_FIELDS = {
    "gender": GENDER_CHOICES,
    "orientation": ORIENTATION_CHOICES,
    "relationship_status": RELATIONSHIP_STATUS_CHOICES,
    "education": EDUCATION_CHOICES,
    "religion": RELIGION_CHOICES,
}
MULTI_CHOICE_FIELDS = {
    "seeking": SEEKING_CHOICES,
}


def _validate_choice_fields(update_data: dict) -> None:
    for field, allowed in CHOICE_FIELDS.items():
        value = update_data.get(field)
        if value is not None and value not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Neplatná hodnota pole '{field}': {value}. Povolené: {allowed}",
            )
    for field, allowed in MULTI_CHOICE_FIELDS.items():
        values = update_data.get(field)
        if values is not None:
            invalid = [v for v in values if v not in allowed]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Neplatné hodnoty pole '{field}': {invalid}. Povolené: {allowed}",
                )


def _get_or_create_profile(db: Session, user_id: int) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    # Staré řádky (před v26) mají tyto sloupce NULL z ALTER TABLE bez
    # DEFAULT - normalizace na 0, ať schema (non-optional int) neselže.
    if profile.profile_views_count is None:
        profile.profile_views_count = 0
    if profile.chat_minutes is None:
        profile.chat_minutes = 0
    return profile


@router.get("/me", response_model=ProfileOut)
def read_my_profile(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    return _get_or_create_profile(db, current_user.id)


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)
    _validate_choice_fields(update_data)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="profile_updated",
        actor_user_id=current_user.id,
        target=current_user.email,
        ip_address=request.client.host if request.client else None,
        meta=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return profile


@router.put("/me/visibility", response_model=ProfileOut)
def update_my_visibility(
    payload: ProfileVisibilityUpdate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Nastaví viditelnost jednotlivých polí profilu, např.
    {"phone": "private", "birth_date": "friends"}. Pole neuvedená ve slovníku
    zůstávají tak, jak byla (výchozí = 'public', pokud nikdy nenastaveno)."""
    profile = _get_or_create_profile(db, current_user.id)

    invalid_fields = [f for f in payload.fields if f not in VISIBILITY_CONTROLLED_FIELDS]
    if invalid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Pro tato pole nelze nastavit viditelnost: {invalid_fields}",
        )
    invalid_levels = {f: v for f, v in payload.fields.items() if v not in VISIBILITY_LEVELS}
    if invalid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Neplatná úroveň viditelnosti: {invalid_levels}. Povolené: {VISIBILITY_LEVELS}",
        )

    current = dict(profile.field_visibility or {})
    current.update(payload.fields)
    profile.field_visibility = current

    db.commit()
    db.refresh(profile)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="profile_visibility_updated",
        actor_user_id=current_user.id,
        target=current_user.email,
        ip_address=request.client.host if request.client else None,
        meta=payload.fields,
    )
    return profile


@router.put("/me/sensitive", response_model=ProfileOut)
def update_my_sensitive_info(
    payload: ProfileSensitiveUpdate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """v29 - Editace citlivých kontaktních/osobních údajů (sekundární email,
    sekundární telefon, datum narození, adresa), mimo běžný formulář "Upravit
    profil". Vyžaduje potvrzení aktuálním heslem (stejný mechanismus jako
    login) - viz DEVLOG #049. Primární `email`/`phone` se tudy NEmění, jsou
    natrvalo needitovatelné."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Nesprávné heslo")

    profile = _get_or_create_profile(db, current_user.id)
    update_data = payload.model_dump(exclude_unset=True, exclude={"current_password"})
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log_event(
        db, LogType.OPERATION_USER_LOG,
        action="profile_sensitive_updated",
        actor_user_id=current_user.id,
        target=current_user.email,
        ip_address=request.client.host if request.client else None,
        # jen názvy měněných polí, ne hodnoty (adresa/kontakty jsou citlivé)
        meta={"fields_changed": list(update_data.keys())},
    )
    return profile


@router.get("/me/locations", response_model=List[ProfileLocationOut])
def list_my_locations(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)
    return profile.locations


@router.post("/me/locations", response_model=ProfileLocationOut, status_code=201)
def add_my_location(
    payload: ProfileLocationCreate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)
    location = ProfileLocation(profile_id=profile.id, **payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.put("/me/locations/{location_id}", response_model=ProfileLocationOut)
def update_my_location(
    location_id: int,
    payload: ProfileLocationUpdate,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)
    location = db.query(ProfileLocation).filter(
        ProfileLocation.id == location_id, ProfileLocation.profile_id == profile.id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Lokace nenalezena")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


@router.delete("/me/locations/{location_id}", status_code=204)
def delete_my_location(
    location_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)
    location = db.query(ProfileLocation).filter(
        ProfileLocation.id == location_id, ProfileLocation.profile_id == profile.id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Lokace nenalezena")
    db.delete(location)
    db.commit()
    return None


@router.get("/{user_id}", response_model=ProfileOut)
def read_public_profile(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: User = Depends(get_current_user_optional),
):
    """Veřejné zobrazení profilu - dostupné i pro guesty (bez auth).
    Pole s viditelností 'friends'/'private' se skrývají (bez auth request
    nejde ověřit přátelství, takže se bezpečně chovají jako neveřejná)."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil nenalezen")
    if profile.profile_views_count is None:
        profile.profile_views_count = 0

    # Čítač zobrazení (v26): prostý +1, jen když se dívá NĚKDO JINÝ než
    # majitel (a ne guest ani samotný majitel) - refresh vlastního profilu
    # ani anonymní scrapování si čítač nenafoukne umělou hodnotou co do
    # "kdo mě viděl", jde jen o hrubý počet cizích zobrazení.
    if viewer is not None and viewer.id != user_id:
        profile.profile_views_count += 1
        db.commit()
        db.refresh(profile)

    out = ProfileOut.model_validate(profile)
    visibility = profile.field_visibility or {}
    for field in VISIBILITY_CONTROLLED_FIELDS:
        if visibility.get(field, "public") != "public":
            setattr(out, field, None if field != "locations" else [])

    # v29: kontaktní/citlivé údaje (birth_date, address, email_secondary,
    # phone_secondary) nejsou součástí field_visibility - skrývají se tu
    # vždy, stejný vzor jako u VISIBILITY_CONTROLLED_FIELDS výše (tento
    # endpoint filtruje bez ohledu na to, jestli je viewer sám majitel -
    # majitel svá data čte přes GET /profile/me, kde se nic nefiltruje).
    for field in ALWAYS_PRIVATE_FIELDS:
        setattr(out, field, None)
    return out


@router.get("/{user_id}/presence", response_model=PresenceOut)
def read_presence(user_id: int, db: Session = Depends(get_db)):
    """Online status + aktuální aktivita, odvozeno live z logů/členství
    (žádný heartbeat) - guest-friendly, stejně jako zbytek veřejného
    profilu."""
    return presence_service.get_presence(db, user_id)
