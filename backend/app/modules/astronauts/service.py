"""Caso de uso: alta de astronautas."""

from __future__ import annotations

from sqlmodel import Session

from app.core import events
from app.domain.errors import ConflictError, NotFoundError
from app.domain.models import Astronaut
from app.infrastructure import repositories


def list_all(session: Session) -> list[Astronaut]:
    return repositories.list_astronauts(session)


def get_one(session: Session, code: str) -> Astronaut:
    astronaut = repositories.get_astronaut(session, code)
    if astronaut is None:
        raise NotFoundError("error.not_found", code=code)
    return astronaut


def create(session: Session, code: str, name: str) -> Astronaut:
    normalized = code.strip().upper()
    if repositories.get_astronaut(session, normalized) is not None:
        raise ConflictError("error.astronaut_exists", code=normalized)
    astronaut = repositories.create_astronaut(session, normalized, name.strip())
    events.bus.publish("astronaut.created", {"astronaut_code": astronaut.code})
    return astronaut


def ensure(session: Session, code: str, name: str) -> Astronaut:
    """Idempotente: crea el astronauta solo si no existe (seed/bootstrap)."""
    existing = repositories.get_astronaut(session, code)
    if existing is not None:
        return existing
    return repositories.create_astronaut(session, code, name)
