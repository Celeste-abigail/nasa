"""Caso de uso: evaluacion y estado de monitoreo por astronauta + sitio."""

from __future__ import annotations

import threading
import time
from datetime import date

from sqlmodel import Session

from app.core.config import settings
from app.core.i18n import level_text, t
from app.domain import bone
from app.domain.models import Measurement
from app.domain.schemas import AssessmentOut, AstronautOut, ModelInfo, PointOut
from app.infrastructure import repositories
from app.modules.measurements.service import ensure_astronaut, thresholds

MODEL_REFERENCES = [
    "https://doi.org/10.1117/12.810048",
    "https://doi.org/10.1016/j.actaastro.2012.08.032",
    "https://doi.org/10.1121/1.4784949",
]
MODEL_FORMULA = "BV/TV = 3.89e-4 * UV - 9e-4 * BUA - 0.456"

_cache: dict[tuple[str, str, str, int | None], tuple[float, AssessmentOut]] = {}
_lock = threading.Lock()


def model_info() -> ModelInfo:
    return ModelInfo(
        version=settings.model_version,
        formula=MODEL_FORMULA,
        references=MODEL_REFERENCES,
    )


def invalidate_cache(*_args, **_kwargs) -> None:
    with _lock:
        _cache.clear()


def _to_point(evaluation: bone.PointEvaluation, lang: str) -> PointOut:
    labels = level_text(lang, evaluation.level)
    return PointOut(
        measured_on=evaluation.measured_on,
        day=evaluation.day,
        bua=evaluation.bua,
        uv=evaluation.uv,
        att=evaluation.att,
        bv_tv=round(evaluation.bv_tv, 6),
        cumulative_loss_pct=round(evaluation.cumulative_loss_pct, 4),
        rate_pct_month=(
            round(evaluation.rate_pct_month, 4) if evaluation.rate_pct_month is not None else None
        ),
        bv_tv_cumulative_loss_pct=round(evaluation.bv_tv_cumulative_loss_pct, 4),
        level=evaluation.level,
        level_name=labels["name"],
        level_tip=labels["tip"],
    )


def _warnings_for(points: list[PointOut], lang: str) -> list[str]:
    messages: list[str] = []
    for point in points:
        if not (0.0 <= point.bv_tv <= 1.0):
            messages.append(
                t(
                    lang,
                    "warning.bv_tv_out_of_range",
                    value=round(point.bv_tv, 4),
                    date=point.measured_on.isoformat(),
                )
            )
    return messages


def build_assessment(
    session: Session,
    code: str,
    site: str,
    lang: str,
    window_months: int | None = None,
) -> AssessmentOut:
    cache_key = (code.upper(), site, lang, window_months)
    if settings.cache_ttl_seconds > 0:
        with _lock:
            cached = _cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < settings.cache_ttl_seconds:
            return cached[1]

    astronaut = ensure_astronaut(session, code)
    measurements: list[Measurement] = repositories.list_measurements(
        session, astronaut.id or 0, site=site
    )
    samples = [
        bone.Sample(measured_on=m.measured_on, bua=m.bua, uv=m.uv, att=m.att) for m in measurements
    ]
    evaluations = bone.evaluate_series(samples, thresholds())
    all_points = [_to_point(item, lang) for item in evaluations]

    visible = all_points
    if window_months and all_points:
        last_day = all_points[-1].measured_on
        limit = window_months * bone.DAYS_PER_MONTH
        visible = [point for point in all_points if (last_day - point.measured_on).days <= limit]
        if all_points[0] not in visible:
            visible = [all_points[0], *visible]

    assessment = AssessmentOut(
        astronaut=AstronautOut(code=astronaut.code, name=astronaut.name),
        site=site,  # type: ignore[arg-type]
        baseline=all_points[0] if all_points else None,
        points=visible,
        current=all_points[-1] if all_points else None,
        warnings=_warnings_for(all_points, lang),
        model=model_info(),
    )

    if settings.cache_ttl_seconds > 0:
        with _lock:
            _cache[cache_key] = (time.monotonic(), assessment)
    return assessment


def latest_measurement_date(session: Session, code: str, site: str) -> date | None:
    astronaut = ensure_astronaut(session, code)
    measurements = repositories.list_measurements(session, astronaut.id or 0, site=site)
    return measurements[-1].measured_on if measurements else None


def preview_point(
    session: Session,
    code: str,
    site: str,
    measured_on: date,
    bua: float,
    uv: float,
    att: float | None,
    lang: str,
) -> PointOut:
    """Evalua una muestra hipotetica contra la serie existente, sin escribir."""
    astronaut = ensure_astronaut(session, code)
    measurements: list[Measurement] = repositories.list_measurements(
        session, astronaut.id or 0, site=site
    )
    samples = [
        bone.Sample(measured_on=m.measured_on, bua=m.bua, uv=m.uv, att=m.att) for m in measurements
    ]
    candidate = bone.Sample(measured_on=measured_on, bua=bua, uv=uv, att=att)
    evaluations = bone.evaluate_series([*samples, candidate], thresholds())
    matches = [item for item in evaluations if item.measured_on == measured_on]
    return _to_point(matches[-1], lang)
