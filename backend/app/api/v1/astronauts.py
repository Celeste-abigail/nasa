from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.domain.schemas import AstronautCreate, AstronautOut
from app.infrastructure.database import get_session
from app.modules.astronauts import service

router = APIRouter(prefix="/astronauts", tags=["astronauts"])


def _out(code: str, name: str) -> AstronautOut:
    return AstronautOut(code=code, name=name)


@router.get("", response_model=list[AstronautOut])
def list_astronauts(session: Session = Depends(get_session)) -> list[AstronautOut]:
    return [_out(a.code, a.name) for a in service.list_all(session)]


@router.post("", response_model=AstronautOut, status_code=status.HTTP_201_CREATED)
def create_astronaut(
    payload: AstronautCreate,
    session: Session = Depends(get_session),
) -> AstronautOut:
    astronaut = service.create(session, payload.code, payload.name)
    return _out(astronaut.code, astronaut.name)


@router.get("/{code}", response_model=AstronautOut)
def get_astronaut(code: str, session: Session = Depends(get_session)) -> AstronautOut:
    astronaut = service.get_one(session, code)
    return _out(astronaut.code, astronaut.name)
