from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# Hardcoded SQLite path (no env variable needed for lab)
DATABASE_URL = "sqlite:///./app.db"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

def get_session() -> Iterator[Session]:
    """FastAPI dependency: ger en DB-session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()