"""
Model ActivitySettings - per-uživatelské nastavení, které typy akcí se
propisují do veřejně viditelné Aktivity na profilu (stejný vzor jako
WallSettings.auto_post_actions u zdi).

`visible_actions` je JSON dict {action_key: bool}, výchozí (chybějící klíč)
= True (viditelné pro ostatní). Majitel profilu a Moderator+ vidí svou/cizí
aktivitu vždy celou bez ohledu na tohle nastavení - jde jen o to, co se
propisuje DÁL, tj. co je vidět veřejně/pro ostatní návštěvníky profilu.
Akce samotná se do OPERATION_USER_LOG / admin (SYSTEM_LOG_FULL) loguje vždy,
tohle nastavení ovlivňuje jen zobrazení v Aktivitě.
"""
from sqlalchemy import Column, Integer, ForeignKey, JSON

from app.db import Base


class ActivitySettings(Base):
    __tablename__ = "activity_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    visible_actions = Column(JSON, nullable=True)  # dict[str, bool]
