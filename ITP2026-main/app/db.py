from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# Sökvägen till SQLite-databasfilen — sparas som app.db i projektmappen
DATABASE_URL = "sqlite:///./app.db"

# SQLite kräver check_same_thread=False för att fungera med FastAPI's async-hantering
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Skapar databasmotorn som hanterar anslutningen till SQLite-filen
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)

# SessionLocal är en fabrik för att skapa nya databassessioner
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base är grunden som alla databasmodeller ärver från — kopplar modeller till databasen
Base = declarative_base()

def get_session() -> Iterator[Session]:
    """FastAPI dependency: ger en DB-session per request."""
    # Öppnar en ny session
    db = SessionLocal()
    try:
        # yield skickar sessionen till routen som använder den
        yield db
    finally:
        # Stänger alltid sessionen efteråt, även om något går fel
        db.close()