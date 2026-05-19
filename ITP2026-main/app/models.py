from __future__ import annotations
import datetime as dt
from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    activities: Mapped[list["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class EmissionFactor(Base):
    """En enkel faktor-tabell: (kategori, nyckel) -> CO2e per enhet."""
    __tablename__ = "emission_factors"
    __table_args__ = (
        UniqueConstraint("category", "key", "unit", name="uq_factor_category_key_unit"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    co2e_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False, default="course_default")
    scope: Mapped[str] = mapped_column(String(20), nullable=True, default="direct")

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    user: Mapped["User"] = relationship(back_populates="activities")