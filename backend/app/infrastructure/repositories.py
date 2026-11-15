"""Repositorios: acceso a datos sin reglas de negocio."""

from __future__ import annotations

from datetime import date, datetime

from sqlmodel import Session, select

from app.domain.models import (
    Astronaut,
    CdaDay,
    CortisolSample,
    Measurement,
    PvtTest,
    RadiationReading,
    SleepNight,
    SleepProfile,
    TlxSession,
    utcnow,
)


def list_astronauts(session: Session, include_archived: bool = False) -> list[Astronaut]:
    stmt = select(Astronaut)
    if not include_archived:
        stmt = stmt.where(Astronaut.deleted_at.is_(None))
    return list(session.exec(stmt.order_by(Astronaut.code)).all())


def list_archived_astronauts(session: Session) -> list[Astronaut]:
    stmt = select(Astronaut).where(Astronaut.deleted_at.is_not(None)).order_by(Astronaut.code)
    return list(session.exec(stmt).all())


def get_astronaut(session: Session, code: str) -> Astronaut | None:
    return session.exec(select(Astronaut).where(Astronaut.code == code)).first()


def create_astronaut(
    session: Session,
    code: str,
    name: str,
    sex: str | None = None,
    birth_date: date | None = None,
) -> Astronaut:
    astronaut = Astronaut(code=code, name=name, sex=sex, birth_date=birth_date)
    session.add(astronaut)
    session.commit()
    session.refresh(astronaut)
    return astronaut


def set_astronaut_archived(session: Session, astronaut: Astronaut, archived: bool) -> Astronaut:
    astronaut.deleted_at = utcnow() if archived else None
    session.add(astronaut)
    session.commit()
    session.refresh(astronaut)
    return astronaut


def list_measurements(
    session: Session,
    astronaut_id: int,
    site: str | None = None,
    since: date | None = None,
) -> list[Measurement]:
    stmt = select(Measurement).where(Measurement.astronaut_id == astronaut_id)
    if site:
        stmt = stmt.where(Measurement.site == site)
    if since:
        stmt = stmt.where(Measurement.measured_on >= since)
    stmt = stmt.order_by(Measurement.measured_on, Measurement.id)
    return list(session.exec(stmt).all())


def add_measurement(
    session: Session,
    astronaut_id: int,
    measured_on: date,
    site: str,
    bua: float,
    uv: float,
    att: float | None,
    source: str = "manual",
) -> Measurement:
    measurement = Measurement(
        astronaut_id=astronaut_id,
        measured_on=measured_on,
        site=site,
        bua=bua,
        uv=uv,
        att=att,
        source=source,
    )
    session.add(measurement)
    session.commit()
    session.refresh(measurement)
    return measurement


def has_measurement_on(session: Session, astronaut_id: int, site: str, day: date) -> bool:
    stmt = select(Measurement).where(
        Measurement.astronaut_id == astronaut_id,
        Measurement.site == site,
        Measurement.measured_on == day,
    )
    return session.exec(stmt).first() is not None


def list_cortisol_samples(
    session: Session,
    astronaut_id: int,
    since: datetime | None = None,
) -> list[CortisolSample]:
    stmt = select(CortisolSample).where(CortisolSample.astronaut_id == astronaut_id)
    if since is not None:
        stmt = stmt.where(CortisolSample.measured_at >= since)
    stmt = stmt.order_by(CortisolSample.measured_at, CortisolSample.id)
    return list(session.exec(stmt).all())


def add_cortisol_sample(
    session: Session,
    astronaut_id: int,
    measured_at: datetime,
    value_ug_dl: float,
    input_value: float,
    input_unit: str,
    wake_time=None,
    mission_phase: str | None = None,
    notes: str | None = None,
    source: str = "manual",
) -> CortisolSample:
    sample = CortisolSample(
        astronaut_id=astronaut_id,
        measured_at=measured_at,
        value_ug_dl=value_ug_dl,
        input_value=input_value,
        input_unit=input_unit,
        wake_time=wake_time,
        mission_phase=mission_phase,
        notes=notes,
        source=source,
    )
    session.add(sample)
    session.commit()
    session.refresh(sample)
    return sample


def list_radiation_readings(session: Session, astronaut_id: int) -> list[RadiationReading]:
    stmt = (
        select(RadiationReading)
        .where(RadiationReading.astronaut_id == astronaut_id)
        .order_by(RadiationReading.measured_at, RadiationReading.id)
    )
    return list(session.exec(stmt).all())


def add_radiation_reading(
    session: Session,
    astronaut_id: int,
    measured_at: datetime,
    eq_rate_usv_min: float,
    dose_rate_ugy_min: float | None,
    region: str,
    module: str | None,
    mission_day: int | None,
    planned_days: int | None,
    prior_career_msv: float | None,
    notes: str | None,
    source: str = "manual",
) -> RadiationReading:
    reading = RadiationReading(
        astronaut_id=astronaut_id,
        measured_at=measured_at,
        eq_rate_usv_min=eq_rate_usv_min,
        dose_rate_ugy_min=dose_rate_ugy_min,
        region=region,
        module=module,
        mission_day=mission_day,
        planned_days=planned_days,
        prior_career_msv=prior_career_msv,
        notes=notes,
        source=source,
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading


def list_tlx_sessions(session: Session, astronaut_id: int) -> list[TlxSession]:
    stmt = (
        select(TlxSession)
        .where(TlxSession.astronaut_id == astronaut_id)
        .order_by(TlxSession.taken_at, TlxSession.id)
    )
    return list(session.exec(stmt).all())


def add_tlx_session(
    session: Session,
    astronaut_id: int,
    taken_at: datetime,
    task_description: str,
    task_category: str,
    duration_min: int | None,
    ratings_json: str,
    comparisons_json: str,
    counts_json: str,
    tlx: float,
    rtlx: float,
    dominant: str,
) -> TlxSession:
    row = TlxSession(
        astronaut_id=astronaut_id,
        taken_at=taken_at,
        task_description=task_description,
        task_category=task_category,
        duration_min=duration_min,
        ratings_json=ratings_json,
        comparisons_json=comparisons_json,
        counts_json=counts_json,
        tlx=tlx,
        rtlx=rtlx,
        dominant=dominant,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_cda_day(session: Session, astronaut_id: int, day: date) -> CdaDay | None:
    stmt = select(CdaDay).where(CdaDay.astronaut_id == astronaut_id, CdaDay.day == day)
    return session.exec(stmt).first()


def list_cda_days(session: Session, astronaut_id: int) -> list[CdaDay]:
    stmt = select(CdaDay).where(CdaDay.astronaut_id == astronaut_id).order_by(CdaDay.day)
    return list(session.exec(stmt).all())


def get_sleep_profile(session: Session, astronaut_id: int) -> SleepProfile | None:
    stmt = select(SleepProfile).where(SleepProfile.astronaut_id == astronaut_id)
    return session.exec(stmt).first()


def list_sleep_nights(session: Session, astronaut_id: int) -> list[SleepNight]:
    stmt = (
        select(SleepNight).where(SleepNight.astronaut_id == astronaut_id).order_by(SleepNight.day)
    )
    return list(session.exec(stmt).all())


def get_sleep_night(session: Session, astronaut_id: int, day: date) -> SleepNight | None:
    stmt = select(SleepNight).where(SleepNight.astronaut_id == astronaut_id, SleepNight.day == day)
    return session.exec(stmt).first()


def list_pvt_tests(session: Session, astronaut_id: int) -> list[PvtTest]:
    stmt = (
        select(PvtTest)
        .where(PvtTest.astronaut_id == astronaut_id)
        .order_by(PvtTest.taken_at, PvtTest.id)
    )
    return list(session.exec(stmt).all())
