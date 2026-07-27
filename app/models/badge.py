"""
Model Badge/UserBadge - odznaky (v25, blok "Vztahy/Odznaky/...", viz DEVLOG #044).

Katalog odznaků je uložen v DB (tabulka `badges`), ne hardcoded jako Enum v
kódu - na žádost uživatele má být editovatelný (admin CRUD, viz
routers/admin.py). `key` je stabilní string identifikátor (ne měnící se
`id`), na který se odkazuje `UserBadge.badge_key` - umožňuje bezpečně
přejmenovat popisek/emoji odznaku bez nutnosti migrovat cizí klíče.

Katalog se seeduje při `init_db()` výchozí sadou 15 odznaků zaměřených na
povahu/vztahový a citový styl (odsouhlaseno s uživatelem) - seed se spustí
jen pokud je tabulka prázdná, aby nepřepisoval pozdější admin úpravy.

`UserBadge` = M:N výběr vlastních odznaků na profilu. Limit max. 5
vybraných najednou je hlídán aplikačně v routeru (ne DB constraintem,
SQLite to neumí čistě), stejný vzor jako max. 1 friend request mezi dvěma
uživateli v `friendship.py`.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.db import Base

# Výchozí katalog (seed) - key, emoji, název. Pořadí = výchozí pořadí zobrazení.
DEFAULT_BADGES = [
    ("romantik", "💞", "Romantik"),
    ("vasnivy", "🔥", "Vášnivý typ"),
    ("klidna_povaha", "🧘", "Klidná povaha"),
    ("oteverna_komunikace", "💬", "Otevřená komunikace"),
    ("empaticky", "🤗", "Empatický/á"),
    ("verny", "🎯", "Věrný/á"),
    ("spontanni", "🌊", "Spontánní"),
    ("ochranitelsky", "🛡️", "Ochranitelský/á"),
    ("vtipalek", "😄", "Vtipálek"),
    ("hravy", "🎭", "Hravý/á"),
    ("trpelivy", "🕰️", "Trpělivý/á"),
    ("charismaticky", "🌟", "Charismatický/á"),
    ("hleda_hlubsi_vztah", "🧩", "Hledá hlubší vztah"),
    ("nezavazny_typ", "🎈", "Nezávazný typ"),
    ("rodinne_orientovany", "🏡", "Rodinně orientovaný/á"),
]


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    emoji = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_key = Column(String, ForeignKey("badges.key"), nullable=False, index=True)
