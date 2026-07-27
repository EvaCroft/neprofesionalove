from datetime import date as _date
from typing import Optional, List

from pydantic import BaseModel, EmailStr

# Povolené hodnoty u výběrových polí profilu. Držet tady na jednom místě
# (ne jako DB Enum) - přidání nové volby je pak jen úprava tohoto seznamu,
# bez DB migrace. "" / None vždy znamená "nechci uvádět".
GENDER_CHOICES = ["muž", "žena", "jiné", "nechci uvádět"]
ORIENTATION_CHOICES = [
    "heterosexuální", "homosexuální", "bisexuální", "pansexuální",
    "asexuální", "jiné", "nechci uvádět",
]
RELATIONSHIP_STATUS_CHOICES = [
    "single", "ve vztahu", "zadaný/á", "manžel/ka", "je to složité", "nechci uvádět",
]
SEEKING_CHOICES = ["přátelství", "vztah", "networking", "nezávazně", "nevím"]
VISIBILITY_LEVELS = ["public", "friends", "private"]

# v29 - Osobní údaje: vzdělání a náboženství, stejný vzor (string + allow-list,
# ne DB Enum). "sexuální preference" (viz níže u ProfileOut/ProfileUpdate) je
# oproti tomu vědomě volný text, ne výběr - viz DEVLOG #049.
EDUCATION_CHOICES = [
    "základní", "vyučen/a", "středoškolské", "vyšší odborné", "vysokoškolské",
    "nechci uvádět",
]
RELIGION_CHOICES = [
    "křesťanství", "islám", "judaismus", "buddhismus", "hinduismus",
    "bez vyznání", "nechci uvádět",
]


class ProfileLocationOut(BaseModel):
    id: int
    label: Optional[str] = None
    city: str
    country: Optional[str] = None
    description: Optional[str] = None
    position: int = 0

    class Config:
        from_attributes = True


class ProfileLocationCreate(BaseModel):
    label: Optional[str] = None
    city: str
    country: Optional[str] = None
    description: Optional[str] = None
    position: int = 0


class ProfileLocationUpdate(BaseModel):
    label: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None


class ProfileVisibilityUpdate(BaseModel):
    """Payload pro PUT /profile/me/visibility: {"phone": "private", "birth_date": "friends"}"""
    fields: dict[str, str]


class ProfileOut(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    bio: Optional[str] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[_date] = None
    gender: Optional[str] = None

    city: Optional[str] = None
    hobbies: Optional[List[str]] = None
    dreams: Optional[str] = None

    orientation: Optional[str] = None
    relationship_status: Optional[str] = None
    seeking: Optional[List[str]] = None

    # --- v29: vzdělání/náboženství (výběr) + sexuální preference (volný text) ---
    education: Optional[str] = None
    religion: Optional[str] = None
    sexual_preference: Optional[str] = None

    # --- v29: rozšířené kontaktní/osobní údaje - vždy jen pro vlastníka,
    # nikdy veřejně (viz `ALWAYS_PRIVATE_FIELDS` v app/models/profile.py a
    # jejich odstranění v app/routers/profile.py:read_public_profile) ---
    email_secondary: Optional[EmailStr] = None
    phone_secondary: Optional[str] = None
    address: Optional[str] = None

    field_visibility: Optional[dict] = None
    locations: List[ProfileLocationOut] = []

    profile_views_count: int = 0
    chat_minutes: int = 0

    # v28a - "Moje statistiky": rozšíření o herní/event/media čísla.
    # Transientní (nepersistované) hodnoty - dopočítávají se v
    # app/routers/profile.py:read_my_profile z existujících tabulek
    # games/events/media, žádná nová DB kolonka. Pro cizí profil
    # (read_public_profile) se nepočítají a zůstávají na výchozí 0.
    games_count: int = 0
    events_count: int = 0
    media_count: int = 0

    class Config:
        from_attributes = True


class ProfileSensitiveUpdate(BaseModel):
    """Payload pro PUT /profile/me/sensitive (v29) - editace citlivých
    kontaktních/osobních údajů vyžaduje potvrzení aktuálním heslem, mimo
    běžný formulář "Upravit profil". `phone`/`email` (primární, přihlašovací
    resp. dřív zavedené kontaktní pole) se tudy NEmění - jsou natrvalo
    needitovatelné, viz DEVLOG #049."""
    current_password: str
    email_secondary: Optional[EmailStr] = None
    phone_secondary: Optional[str] = None
    birth_date: Optional[_date] = None
    address: Optional[str] = None


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    bio: Optional[str] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    # POZN. (v29): `phone` a `birth_date` tu záměrně CHYBÍ - `phone` je od
    # v29 natrvalo needitovatelný (žádná cesta v API ho nemění), `birth_date`
    # se přesunul do `ProfileSensitiveUpdate` (PUT /profile/me/sensitive,
    # vyžaduje heslo). Viz DEVLOG #049.
    gender: Optional[str] = None

    city: Optional[str] = None
    hobbies: Optional[List[str]] = None
    dreams: Optional[str] = None

    orientation: Optional[str] = None
    relationship_status: Optional[str] = None
    seeking: Optional[List[str]] = None

    education: Optional[str] = None
    religion: Optional[str] = None
    sexual_preference: Optional[str] = None
