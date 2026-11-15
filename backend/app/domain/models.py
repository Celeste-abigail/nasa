"""Modelos de persistencia (SQLModel)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import Column, Date, DateTime, String, Text, Time, UniqueConstraint
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
    # Archivado (soft delete): conserva todos los datos para poder restaurarlo.
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))
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


class RadiationReading(SQLModel, table=True):
    """Lectura de radiacion (TEPC). Seccion independiente."""

    __tablename__ = "radiation_reading"

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    measured_at: datetime = Field(sa_column=Column(DateTime, index=True, nullable=False))
    eq_rate_usv_min: float
    dose_rate_ugy_min: float | None = None
    region: str = Field(default="unknown", sa_column=Column(String(8), nullable=False))
    module: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    mission_day: int | None = None
    planned_days: int | None = None
    prior_career_msv: float | None = None
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    source: str = Field(default="manual", sa_column=Column(String(16), nullable=False))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, nullable=False),
    )


class TlxSession(SQLModel, table=True):
    __tablename__ = "tlx_session"

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    taken_at: datetime = Field(sa_column=Column(DateTime, index=True, nullable=False))
    task_description: str = Field(sa_column=Column(String(300), nullable=False))
    task_category: str = Field(sa_column=Column(String(64), nullable=False))
    duration_min: int | None = None
    ratings_json: str = Field(sa_column=Column(Text, nullable=False))
    comparisons_json: str = Field(sa_column=Column(Text, nullable=False))
    counts_json: str = Field(sa_column=Column(Text, nullable=False))
    tlx: float
    rtlx: float
    dominant: str = Field(sa_column=Column(String(2), nullable=False))


class CdaDay(SQLModel, table=True):
    __tablename__ = "cda_day"
    __table_args__ = (UniqueConstraint("astronaut_id", "day", name="uq_cda_day"),)

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    day: date = Field(sa_column=Column(Date, index=True, nullable=False))
    items_json: str = Field(sa_column=Column(Text, nullable=False))
    adjusted_json: str = Field(sa_column=Column(Text, nullable=False))
    iad: float
    positive: float
    negative: float
    stress_fatigue: float
    sleep: float
    connection: float


class SleepProfile(SQLModel, table=True):
    __tablename__ = "sleep_profile"
    __table_args__ = (UniqueConstraint("astronaut_id", name="uq_sleep_profile_astronaut"),)

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    need_hours: float = 7.5
    scheduled_wake: str = Field(default="06:00", sa_column=Column(String(5), nullable=False))
    window_minutes: int = 450
    last_adjustment: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    blocked: bool = False


class SleepNight(SQLModel, table=True):
    __tablename__ = "sleep_night"
    __table_args__ = (UniqueConstraint("astronaut_id", "day", name="uq_sleep_night"),)

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    day: date = Field(sa_column=Column(Date, index=True, nullable=False))
    entry_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    latency_min: int
    awakenings: int
    waso_min: int
    cause_group: str | None = Field(default=None, sa_column=Column(String(1), nullable=True))
    cause_detail: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    final_wake_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    exit_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    quality: int
    inertia: int
    dreams: str = Field(sa_column=Column(String(16), nullable=False))
    environmental_json: str = Field(sa_column=Column(Text, nullable=False))
    nap_min: int | None = None
    tib_min: float
    tst_min: float
    efficiency: float
    midpoint_at: datetime = Field(sa_column=Column(DateTime, nullable=False))


class PvtTest(SQLModel, table=True):
    __tablename__ = "pvt_test"

    id: int | None = Field(default=None, primary_key=True)
    astronaut_id: int = Field(foreign_key="astronaut.id", index=True)
    taken_at: datetime = Field(sa_column=Column(DateTime, index=True, nullable=False))
    mode: int
    trials_json: str = Field(sa_column=Column(Text, nullable=False))
    input_false_starts: int = 0
    valid_count: int
    lapses: int
    false_starts: int
    mean_rt_ms: float
    speed: float
    subjective_alertness: int | None = None
    z: float | None = None
    color: int | None = None
