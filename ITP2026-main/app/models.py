from __future__ import annotations
import datetime as dt
from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

# User representerar en användare i systemet
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # En användare kan ha många aktiviteter — cascade betyder att aktiviteter raderas om användaren raderas
    activities: Mapped[list["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# EmissionFactor innehåller utsläppsfaktorer — varje rad är en kombination av kategori och nyckel
class EmissionFactor(Base):
    """En enkel faktor-tabell: (kategori, nyckel) -> CO2e per enhet."""
    __tablename__ = "emission_factors"

    # UniqueConstraint säkerställer att samma kombination av kategori+nyckel+enhet inte kan sparas två gånger
    __table_args__ = (
        UniqueConstraint("category", "key", "unit", name="uq_factor_category_key_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)   # t.ex. "transport"
    key: Mapped[str] = mapped_column(String(60), nullable=False)         # t.ex. "car"
    unit: Mapped[str] = mapped_column(String(20), nullable=False)        # t.ex. "km"
    co2e_per_unit: Mapped[float] = mapped_column(Float, nullable=False)  # kg CO₂e per enhet
    source: Mapped[str] = mapped_column(String(200), nullable=False, default="course_default")
    scope: Mapped[str] = mapped_column(String(20), nullable=True, default="direct")

# Activity representerar en loggad aktivitet kopplad till en användare
class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  # Främmande nyckel till users-tabellen
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)   # Mängd i enhetens enhet, t.ex. antal km
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)

    # Relation tillbaka till användaren — gör att man kan skriva aktivitet.user.name
    user: Mapped["User"] = relationship(back_populates="activities")