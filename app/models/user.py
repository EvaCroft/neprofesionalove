"""
Model User + Role.

Role "guest" existuje jen jako logický koncept neautentizovaného návštěvníka
(nemá záznam v tabulce users) - viz app/permissions.py (v2). Zde jsou role
pro registrované účty.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Enum

from app.db import Base


class RoleEnum(str, enum.Enum):
    USER = "user"
    CREATOR = "creator"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.USER)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
