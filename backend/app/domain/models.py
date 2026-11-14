"""Modelos de persistencia (SQLModel)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Column, Date, DateTime, String
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """UTC naive: SQLite no guarda zona horaria."""
    return datetime.now(UTC).replace(tzinfo=None)


class Astronaut(SQLModel, table=True):
    __tablename__ = "astronaut"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(sa_column=Column(String(32), unique=True, index=True, nullable=False))
    name: str = Field(default="", sa_column=Column(String(120), nullable=False, default=""))
    # Perfil para la referencia poblacional. Nullable para no romper datos previos.
    sex: str | None = Field(default=None, sa_column=Column(String(8), nullable=True))
    birth_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, nullable=False),
    )


class Measurement(SQLModel, table=True):
    __tablename__ = "measurement"

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    measured_on: date = Field(sa_column=Column(Date, index=True, nullable=False))
    site: str = Field(sa_column=Column(String(32), index=True, nullable=False))
    bua: float
    uv: float
    att: float | None = None
    source: str = Field(default="manual", sa_column=Column(String(16), nullable=False))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
