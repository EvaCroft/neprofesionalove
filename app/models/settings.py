"""Globální systémová nastavení - jednoduchý key-value store spravovaný adminem."""
from sqlalchemy import Column, String, Text

from app.db import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
