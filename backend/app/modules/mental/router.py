from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api.deps import get_lang
from app.domain.schemas import (
    CdaInput,
    CdaPointOut,
    MentalAssessmentOut,
    PvtInput,
    PvtOut,
    SleepNightIn,
    SleepNightOut,
    SleepProfileIn,
    SleepProfileOut,
    TlxSessionCreate,
    TlxSessionOut,
)
from app.infrastructure.database import get_session
from app.modules.mental import service

router = APIRouter(prefix="/astronauts/{code}/mental", tags=["mental"])


@router.get("", response_model=MentalAssessmentOut)
def get_mental(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> MentalAssessmentOut:
    return service.build_assessment(session, code, lang)


@router.post("/tlx", response_model=TlxSessionOut, status_code=status.HTTP_201_CREATED)
def create_tlx(
    code: str,
    payload: TlxSessionCreate,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> TlxSessionOut:
    return service.record_tlx(session, code, payload, lang)


@router.put("/cda/{day}", response_model=CdaPointOut)
def save_cda(
    code: str,
    day: date,
    payload: CdaInput,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> CdaPointOut:
    return service.upsert_cda(session, code, day, payload, lang)


@router.get("/sleep/profile", response_model=SleepProfileOut)
def get_sleep_profile(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> SleepProfileOut:
    return service.profile_out(session, code)


@router.put("/sleep/profile", response_model=SleepProfileOut)
def save_sleep_profile(
    code: str,
    payload: SleepProfileIn,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> SleepProfileOut:
    return service.save_profile(session, code, payload, lang)


@router.put("/sleep/{day}", response_model=SleepNightOut)
def save_sleep_night(
    code: str,
    day: date,
    payload: SleepNightIn,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> SleepNightOut:
    payload = payload.model_copy(update={"day": day})
    return service.upsert_sleep(session, code, payload, lang)


@router.post("/pvt", response_model=PvtOut, status_code=status.HTTP_201_CREATED)
def create_pvt(
    code: str,
    payload: PvtInput,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> PvtOut:
    return service.record_pvt(session, code, payload, lang)
