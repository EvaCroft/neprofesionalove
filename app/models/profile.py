"""
Model Profile - základní i rozšířené info k uživateli (odděleno od User
kvůli oddělení auth dat od veřejně zobrazitelných dat).

Rozšířená pole (v20+, "Dokončení uživatelského profilu") jsou vědomě
uložena jako prosté nullable sloupce (ne SQLAlchemy Enum) - přidání nové
volby (např. nová hodnota u orientace) tak nevyžaduje DB migraci, jen
úpravu seznamu povolených hodnot v `app/schemas.py`. Vícehodnotová pole
(záliby, hledám) jsou JSON seznam stringů ve sloupci typu JSON.

`field_visibility` je JSON slovník {nazev_pole: "public"|"friends"|"private"}.
Pole, které v něm chybí, se bere jako "public" (výchozí) - viz
`app/services/profile_visibility.py`.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship

from app.db import Base

# Pole profilu, u kterých dává smysl nastavit viditelnost (sekce "O mně" +
# citlivé údaje). Držet na jednom místě, ať se seznam nerozjede mezi
# modelem/schématy/routerem.
VISIBILITY_CONTROLLED_FIELDS = [
    "first_name", "last_name", "nickname", "phone", "gender",
    "city", "bio", "hobbies", "dreams", "orientation", "relationship_status",
    "seeking", "locations", "education", "religion", "sexual_preference",
]

# v29: kontaktní/citlivé osobní údaje, které se NIKDY nevrací mimo vlastníka
# (bez ohledu na field_visibility) - needitovatelné přes běžný formulář
# "Upravit profil", měnitelné jen přes PUT /profile/me/sensitive (heslo).
# `birth_date` sem přešel z VISIBILITY_CONTROLLED_FIELDS (byl tam od v20,
# šlo nastavit public/friends/private) - od v29 je vždy jen pro vlastníka,
# viz DEVLOG #049 (rozhodnutí spec-first s uživatelem).
ALWAYS_PRIVATE_FIELDS = ["birth_date", "address", "email_secondary", "phone_secondary"]


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # --- základ (v2) ---
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # --- přítomnost / čítače (v26) ---
    profile_views_count = Column(Integer, nullable=False, default=0)
    chat_minutes = Column(Integer, nullable=False, default=0)

    # --- rozšíření v20+ ---
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String, nullable=True)  # volný string, povolené hodnoty viz schemas.py

    city = Column(String, nullable=True)  # hlavní/primární město (zpětná kompatibilita); další viz ProfileLocation

    hobbies = Column(JSON, nullable=True)  # list[str]
    dreams = Column(Text, nullable=True)

    orientation = Column(String, nullable=True)
    relationship_status = Column(String, nullable=True)
    seeking = Column(JSON, nullable=True)  # list[str]

    # --- v29: vzdělání/náboženství (výběr, allow-list v schemas.py) +
    # sexuální preference (vědomě volný text, ne výběr - viz DEVLOG #049) ---
    education = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    sexual_preference = Column(Text, nullable=True)

    # --- v29: rozšířené kontaktní údaje - viz ALWAYS_PRIVATE_FIELDS výše.
    # Měnitelné jen přes PUT /profile/me/sensitive (vyžaduje heslo). Primární
    # `phone` (nahoře) zůstává čitelné pole, ale od v29 už není editovatelné
    # žádnou cestou v API (needitovatelné natrvalo, stejně jako User.email). ---
    email_secondary = Column(String, nullable=True)
    phone_secondary = Column(String, nullable=True)
    address = Column(String, nullable=True)

    cover_url = Column(String, nullable=True)  # úvodní/cover obrázek (fallback URL - v21 se propojí s Médii)

    field_visibility = Column(JSON, nullable=True)  # dict[str, "public"|"friends"|"private"]

    locations = relationship(
        "ProfileLocation", order_by="ProfileLocation.position",
        cascade="all, delete-orphan",
    )
