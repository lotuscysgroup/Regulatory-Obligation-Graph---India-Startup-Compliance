from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    type_annotation_map: dict[Any, Any] = {}


_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_engine(database_url: str) -> Engine:
    global _engine, SessionLocal

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine().")
    return _engine


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Session factory not initialized. Call init_engine().")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

