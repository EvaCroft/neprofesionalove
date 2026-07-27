"""
Model Follow - jednosměrné sledování (v24, blok "Vztahy").

Nezávislé na `FriendRequest` (viz DEVLOG rozhodnutí #044: "obojí zvlášť") -
sledovat lze kohokoliv bez schvalování, i bez vzájemného přátelství, a
naopak přátelství samo o sobě sledování nezakládá. Odsledování rovnou maže
řádek (žádná historie).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint

from app.db import Base


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),)

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # kdo sleduje
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # koho sleduje
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
