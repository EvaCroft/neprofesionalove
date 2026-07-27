"""
Model ProfileLocation - rozšiřitelný seznam lokací u profilu.

Na žádost uživatele (2026-07-26): "u lokace by to chtelo udelat rozsiritelny,
uzivatel prida lokaci2 lokaci3 i s popisem dane lokace" - proto samostatná
tabulka 1:N k Profile místo pevného počtu sloupců (city/city2/city3...).
Profile.city zůstává jako rychlý/primární fallback (zobrazovaný v hlavičce
profilu), ProfileLocation je plný rozšiřitelný seznam.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime

from app.db import Base


class ProfileLocation(Base):
    __tablename__ = "profile_locations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)

    label = Column(String, nullable=True)       # např. "Domov", "Práce", "Chalupa"
    city = Column(String, nullable=False)
    country = Column(String, nullable=True)
    description = Column(Text, nullable=True)   # volný popis dané lokace
    position = Column(Integer, nullable=False, default=0)  # pořadí zobrazení

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
