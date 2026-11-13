"""Conexion a SQLite. La base la levanta uvicorn en el lifespan de la app."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

_engine: Engine | None = None


def _ensure_sqlite_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    raw = url.removeprefix("sqlite:///")
    Path(raw).parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _ensure_sqlite_dir(settings.database_url)
        connect_args = (
            {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        )
        _engine = create_engine(
            settings.database_url, connect_args=connect_args, pool_pre_ping=True
        )
    return _engine


def init_db() -> None:
    """Crea el archivo .db y las tablas si no existen."""
    from app.domain import models  # noqa: F401  (registra las tablas en el metadata)

    SQLModel.metadata.create_all(get_engine())


def dispose_db() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
