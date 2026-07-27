"""
Model WallSettings - per-uživatelské nastavení, které akce se automaticky
propisují na jeho zeď jako Post (origin=SYSTEM_GENERATED).

`auto_post_actions` je JSON dict {action_key: bool}, výchozí (chybějící
klíč) = True (propisuje se), viz WALL_ACTION_KEYS ve schemas.py - stejný
vzor jako `field_visibility` u Profile.
"""
from sqlalchemy import Column, Integer, ForeignKey, JSON

from app.db import Base


class WallSettings(Base):
    __tablename__ = "wall_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    auto_post_actions = Column(JSON, nullable=True)  # dict[str, bool]
