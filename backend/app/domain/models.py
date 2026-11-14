"""Modelos de persistencia (SQLModel)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import Column, Date, DateTime, String, Text, Time
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


class CortisolSample(SQLModel, table=True):
    """Muestra de cortisol salival (CLIA/ECLIA). Independiente del modulo oseo."""

    __tablename__ = "cortisol_sample"

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    measured_at: datetime = Field(sa_column=Column(DateTime, index=True, nullable=False))
    value_ug_dl: float
    input_value: float
    input_unit: str = Field(sa_column=Column(String(8), nullable=False))
    wake_time: time | None = Field(default=None, sa_column=Column(Time, nullable=True))
    mission_phase: str | None = Field(default=None, sa_column=Column(String(16), nullable=True))
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    source: str = Field(default="manual", sa_column=Column(String(16), nullable=False))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
