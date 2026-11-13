"""Repositorios: acceso a datos sin reglas de negocio."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from app.domain.models import Astronaut, Measurement


def list_astronauts(session: Session) -> list[Astronaut]:
    return list(session.exec(select(Astronaut).order_by(Astronaut.code)).all())


def get_astronaut(session: Session, code: str) -> Astronaut | None:
    return session.exec(select(Astronaut).where(Astronaut.code == code)).first()


def create_astronaut(session: Session, code: str, name: str) -> Astronaut:
    astronaut = Astronaut(code=code, name=name)
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
