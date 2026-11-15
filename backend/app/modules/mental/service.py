"""Caso de uso del modulo de salud mental (TLX + CDA + sueno + PVT)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from sqlmodel import Session

from app.domain import mental
from app.domain.errors import ValidationError
from app.domain.models import CdaDay, PvtTest, SleepNight, SleepProfile, TlxSession
from app.domain.schemas import (
    CdaInput,
    CdaPointOut,
    MentalAssessmentOut,
    PrescriptionOut,
    PvtInput,
    PvtOut,
    SleepNightIn,
    SleepNightOut,
    SleepProfileIn,
    SleepProfileOut,
    TlxPointOut,
    TlxSessionCreate,
    TlxSessionOut,
)
from app.infrastructure import repositories
from app.modules.astronauts import service as astronauts_service


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load(value: str | None) -> object:
    return json.loads(value) if value else None


def _tlx_out(row: TlxSession) -> TlxSessionOut:
    ratings = _load(row.ratings_json) or {}
    counts = _load(row.counts_json) or {}
    weights = {dimension: counts.get(dimension, 0) / 15.0 for dimension in mental.DIMENSIONS}
    contributions = {
        dimension: int(ratings.get(dimension, 0)) * counts.get(dimension, 0) / 15.0
        for dimension in mental.DIMENSIONS
    }
    return TlxSessionOut(
        id=row.id or 0,
        taken_at=row.taken_at,
        task_description=row.task_description,
        task_category=row.task_category,
        duration_min=row.duration_min,
        ratings={key: int(value) for key, value in ratings.items()},
        counts={key: int(value) for key, value in counts.items()},
        weights={key: round(value, 4) for key, value in weights.items()},
        contributions={key: round(value, 2) for key, value in contributions.items()},
        tlx=round(row.tlx, 2),
        rtlx=round(row.rtlx, 2),
        dominant=row.dominant,
    )


def _tlx_point_out(point: mental.TlxPoint) -> TlxPointOut:
    return TlxPointOut(
        index=point.index,
        taken_at=point.taken_at,
        tlx=point.tlx,
        rtlx=point.rtlx,
        dominant=point.dominant,
        color=point.color,
        phase=point.phase,
        z=point.z,
        ewma=point.ewma,
        se=point.se,
        limit_warn=point.limit_warn,
        limit_action=point.limit_action,
        underload=point.underload,
    )


def _cda_point_out(row: CdaDay, point: mental.CdaPoint) -> CdaPointOut:
    return CdaPointOut(
        day=row.day,
        iad=round(row.iad, 2),
        positive=round(row.positive, 2),
        negative=round(row.negative, 2),
        stress_fatigue=round(row.stress_fatigue, 2),
        sleep=round(row.sleep, 2),
        connection=round(row.connection, 2),
        color=point.color,
        phase=point.phase,
        mm7=point.mm7,
        z=point.z,
        flags=list(point.flags),
    )


def _sleep_out(row: SleepNight, point: mental.SleepPoint) -> SleepNightOut:
    return SleepNightOut(
        day=row.day,
        entry_at=row.entry_at,
        final_wake_at=row.final_wake_at,
        exit_at=row.exit_at,
        latency_min=row.latency_min,
        awakenings=row.awakenings,
        waso_min=row.waso_min,
        cause_group=row.cause_group,
        cause_detail=row.cause_detail,
        quality=row.quality,
        inertia=row.inertia,
        dreams=row.dreams,
        environmental=list(_load(row.environmental_json) or []),
        nap_min=row.nap_min,
        tib_min=row.tib_min,
        tst_min=row.tst_min,
        efficiency=row.efficiency,
        midpoint_at=row.midpoint_at,
        color=point.color,
        flags=list(point.flags),
        debt_hours=point.debt_hours,
        se7=point.se7,
        midpoint_shift_min=point.midpoint_shift_min,
        excluded=point.excluded,
    )


def _pvt_out(row: PvtTest) -> PvtOut:
    z = row.z
    discrepancy = bool(
        row.subjective_alertness is not None
        and row.subjective_alertness >= 7
        and z is not None
        and z <= -1
    )
    return PvtOut(
        id=row.id or 0,
        taken_at=row.taken_at,
        mode=row.mode,
        valid_count=row.valid_count,
        lapses=row.lapses,
        false_starts=row.false_starts,
        mean_rt_ms=round(row.mean_rt_ms, 2),
        speed=round(row.speed, 3),
        subjective_alertness=row.subjective_alertness,
        z=None if z is None else round(z, 2),
        color=row.color,
        discrepancy=discrepancy,
    )


def _profile_out(profile: SleepProfile) -> SleepProfileOut:
    return SleepProfileOut(
        need_hours=profile.need_hours,
        scheduled_wake=profile.scheduled_wake,
        window_minutes=profile.window_minutes,
        last_adjustment=profile.last_adjustment,
        blocked=profile.blocked,
    )


def get_profile(session: Session, astronaut_id: int) -> SleepProfile:
    profile = repositories.get_sleep_profile(session, astronaut_id)
    if profile is None:
        profile = SleepProfile(astronaut_id=astronaut_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def profile_out(session: Session, code: str) -> SleepProfileOut:
    astronaut = astronauts_service.get_one(session, code)
    return _profile_out(get_profile(session, astronaut.id or 0))


def record_tlx(session: Session, code: str, payload: TlxSessionCreate, lang: str) -> TlxSessionOut:
    astronaut = astronauts_service.get_one(session, code)
    taken_at = payload.taken_at or datetime.now()
    comparisons = [{"pair": list(item.pair), "choice": item.choice} for item in payload.comparisons]
    try:
        result = mental.score_tlx(payload.ratings, comparisons)
    except ValueError as exc:
        raise ValidationError("error.tlx_invalid", detail=str(exc)) from exc

    row = repositories.add_tlx_session(
        session=session,
        astronaut_id=astronaut.id or 0,
        taken_at=taken_at.replace(second=0, microsecond=0),
        task_description=payload.task_description.strip(),
        task_category=payload.task_category,
        duration_min=payload.duration_min,
        ratings_json=_dump(result.ratings),
        comparisons_json=_dump(comparisons),
        counts_json=_dump(result.counts),
        tlx=result.tlx,
        rtlx=result.rtlx,
        dominant=result.dominant,
    )
    return _tlx_out(row)


def upsert_cda(session: Session, code: str, day: date, payload: CdaInput, lang: str) -> CdaPointOut:
    astronaut = astronauts_service.get_one(session, code)
    if day > date.today():
        raise ValidationError("error.day_future")
    try:
        score = mental.score_cda(payload.items)
    except ValueError as exc:
        raise ValidationError("error.cda_invalid", detail=str(exc)) from exc

    row = repositories.get_cda_day(session, astronaut.id or 0, day)
    if row is None:
        row = CdaDay(
            astronaut_id=astronaut.id or 0,
            day=day,
            items_json=_dump(payload.items),
            adjusted_json=_dump(score.adjusted),
            iad=score.iad,
            positive=score.positive,
            negative=score.negative,
            stress_fatigue=score.stress_fatigue,
            sleep=score.sleep,
            connection=score.connection,
        )
    else:
        row.items_json = _dump(payload.items)
        row.adjusted_json = _dump(score.adjusted)
        row.iad = score.iad
        row.positive = score.positive
        row.negative = score.negative
        row.stress_fatigue = score.stress_fatigue
        row.sleep = score.sleep
        row.connection = score.connection
    session.add(row)
    session.commit()
    session.refresh(row)

    rows = repositories.list_cda_days(session, astronaut.id or 0)
    points = mental.evaluate_cda_series([(item.day, item.iad) for item in rows])
    point = next(item for item in points if item.day == day)
    return _cda_point_out(row, point)


def save_profile(
    session: Session, code: str, payload: SleepProfileIn, lang: str
) -> SleepProfileOut:
    astronaut = astronauts_service.get_one(session, code)
    profile = get_profile(session, astronaut.id or 0)
    profile.need_hours = payload.need_hours
    profile.scheduled_wake = payload.scheduled_wake
    profile.window_minutes = payload.window_minutes
    profile.blocked = payload.blocked
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return _profile_out(profile)


def upsert_sleep(session: Session, code: str, payload: SleepNightIn, lang: str) -> SleepNightOut:
    astronaut = astronauts_service.get_one(session, code)
    if payload.day > date.today():
        raise ValidationError("error.day_future")
    try:
        metrics = mental.night_metrics(
            payload.entry_at,
            payload.latency_min,
            payload.waso_min,
            payload.final_wake_at,
            payload.exit_at,
        )
    except ValueError as exc:
        raise ValidationError("error.sleep_invalid", detail=str(exc)) from exc

    row = repositories.get_sleep_night(session, astronaut.id or 0, payload.day)
    if row is None:
        row = SleepNight(
            astronaut_id=astronaut.id or 0,
            day=payload.day,
            entry_at=payload.entry_at,
            latency_min=payload.latency_min,
            awakenings=payload.awakenings,
            waso_min=payload.waso_min,
            cause_group=payload.cause_group,
            cause_detail=payload.cause_detail,
            final_wake_at=payload.final_wake_at,
            exit_at=payload.exit_at,
            quality=payload.quality,
            inertia=payload.inertia,
            dreams=payload.dreams,
            environmental_json=_dump(payload.environmental),
            nap_min=payload.nap_min,
            tib_min=metrics.tib_min,
            tst_min=metrics.tst_min,
            efficiency=metrics.efficiency,
            midpoint_at=metrics.midpoint_at,
        )
    else:
        row.entry_at = payload.entry_at
        row.latency_min = payload.latency_min
        row.awakenings = payload.awakenings
        row.waso_min = payload.waso_min
        row.cause_group = payload.cause_group
        row.cause_detail = payload.cause_detail
        row.final_wake_at = payload.final_wake_at
        row.exit_at = payload.exit_at
        row.quality = payload.quality
        row.inertia = payload.inertia
        row.dreams = payload.dreams
        row.environmental_json = _dump(payload.environmental)
        row.nap_min = payload.nap_min
        row.tib_min = metrics.tib_min
        row.tst_min = metrics.tst_min
        row.efficiency = metrics.efficiency
        row.midpoint_at = metrics.midpoint_at
    session.add(row)
    session.commit()
    session.refresh(row)

    return _sleep_out_for(session, astronaut.id or 0, row, get_profile(session, astronaut.id or 0))


def _sleep_out_for(
    session: Session, astronaut_id: int, row: SleepNight, profile: SleepProfile
) -> SleepNightOut:
    rows = repositories.list_sleep_nights(session, astronaut_id)
    inputs = [
        mental.SleepNightInput(
            day=item.day,
            tst_min=item.tst_min,
            efficiency=item.efficiency,
            midpoint_at=item.midpoint_at,
            inertia=item.inertia,
            environmental=tuple(_load(item.environmental_json) or []),
        )
        for item in rows
    ]
    points = mental.evaluate_sleep_series(inputs, profile.need_hours)
    point = next(item for item in points if item.day == row.day)
    return _sleep_out(row, point)


def record_pvt(session: Session, code: str, payload: PvtInput, lang: str) -> PvtOut:
    astronaut = astronauts_service.get_one(session, code)
    if not payload.trials:
        raise ValidationError("error.pvt_invalid", detail="no trials")
    metrics = mental.pvt_metrics(payload.trials, payload.false_starts)
    prior = repositories.list_pvt_tests(session, astronaut.id or 0)
    color, z = mental.pvt_alert(float(metrics["speed"]), [row.speed for row in prior])

    row = PvtTest(
        astronaut_id=astronaut.id or 0,
        taken_at=(payload.taken_at or datetime.now()).replace(second=0, microsecond=0),
        mode=payload.mode,
        trials_json=_dump(payload.trials),
        input_false_starts=payload.false_starts,
        valid_count=int(metrics["valid_count"]),
        lapses=int(metrics["lapses"]),
        false_starts=int(metrics["false_starts"]),
        mean_rt_ms=float(metrics["mean_rt_ms"]),
        speed=float(metrics["speed"]),
        subjective_alertness=payload.subjective_alertness,
        z=z,
        color=color,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _pvt_out(row)


def _adherence(
    session: Session,
    astronaut_id: int,
    tlx: list[TlxSession],
    cda: list[CdaDay],
    sleep: list[SleepNight],
    pvt: list[PvtTest],
) -> dict[str, int]:
    since = datetime.now() - timedelta(days=7)
    since_day = date.today() - timedelta(days=7)
    return {
        "tlx_sessions": sum(1 for row in tlx if row.taken_at >= since),
        "cda_days": sum(1 for row in cda if row.day >= since_day),
        "sleep_nights": sum(1 for row in sleep if row.day >= since_day),
        "pvt_tests": sum(1 for row in pvt if row.taken_at >= since),
    }


def build_assessment(session: Session, code: str, lang: str) -> MentalAssessmentOut:
    astronaut = astronauts_service.get_one(session, code)
    astronaut_id = astronaut.id or 0
    profile = get_profile(session, astronaut_id)

    tlx_rows = repositories.list_tlx_sessions(session, astronaut_id)
    tlx_out = [_tlx_out(row) for row in tlx_rows]
    tlx_points = [
        _tlx_point_out(point)
        for point in mental.evaluate_tlx_series(
            [(row.taken_at, row.tlx, row.rtlx, row.dominant) for row in tlx_rows]
        )
    ]

    cda_rows = repositories.list_cda_days(session, astronaut_id)
    cda_points_raw = mental.evaluate_cda_series([(row.day, row.iad) for row in cda_rows])
    cda_by_day = {row.day: row for row in cda_rows}
    cda_points = [_cda_point_out(cda_by_day[point.day], point) for point in cda_points_raw]

    sleep_rows = repositories.list_sleep_nights(session, astronaut_id)
    sleep_inputs = [
        mental.SleepNightInput(
            day=row.day,
            tst_min=row.tst_min,
            efficiency=row.efficiency,
            midpoint_at=row.midpoint_at,
            inertia=row.inertia,
            environmental=tuple(_load(row.environmental_json) or []),
        )
        for row in sleep_rows
    ]
    sleep_points_raw = mental.evaluate_sleep_series(sleep_inputs, profile.need_hours)
    sleep_by_day = {row.day: row for row in sleep_rows}
    sleep_points = [_sleep_out(sleep_by_day[point.day], point) for point in sleep_points_raw]

    pvt_rows = repositories.list_pvt_tests(session, astronaut_id)
    pvt_points = [_pvt_out(row) for row in pvt_rows]

    current_tlx = tlx_out[-1] if tlx_out else None
    current_tlx_point = tlx_points[-1] if tlx_points else None
    current_cda = cda_points[-1] if cda_points else None
    current_sleep = sleep_points[-1] if sleep_points else None
    current_pvt = pvt_points[-1] if pvt_points else None

    global_color = mental.worst_color(
        current_tlx_point.color if current_tlx_point else None,
        current_cda.color if current_cda else None,
        current_sleep.color if current_sleep else None,
        current_pvt.color if current_pvt else None,
    )

    profile_out = _profile_out(profile)
    window_suggestion = mental.suggest_window(
        profile.window_minutes,
        current_sleep.se7 if current_sleep else None,
        profile.need_hours,
        profile.blocked,
    )

    prescriptions = mental.prescription_ids(
        se7=current_sleep.se7 if current_sleep else None,
        last_cause=current_sleep.cause_group if current_sleep else None,
        inertia=current_sleep.inertia if current_sleep else None,
        dreams=current_sleep.dreams if current_sleep else None,
        environmental=current_sleep.environmental if current_sleep else None,
        pvt_color=current_pvt.color if current_pvt else None,
        debt_hours=current_sleep.debt_hours if current_sleep else None,
        midpoint_shift_min=current_sleep.midpoint_shift_min if current_sleep else None,
        subjective_alertness=current_pvt.subjective_alertness if current_pvt else None,
        pvt_z=current_pvt.z if current_pvt else None,
    )

    return MentalAssessmentOut(
        astronaut=astronauts_service.to_out(astronaut),
        tlx_points=tlx_points,
        cda_days=cda_points,
        sleep_nights=sleep_points,
        pvt_tests=pvt_points,
        current_tlx=current_tlx,
        current_cda=current_cda,
        current_sleep=current_sleep,
        current_pvt=current_pvt,
        global_color=global_color,
        prescriptions=[PrescriptionOut(**item) for item in prescriptions],
        sleep_profile=profile_out,
        window_suggestion=window_suggestion,
        adherence=_adherence(session, astronaut_id, tlx_rows, cda_rows, sleep_rows, pvt_rows),
        privacy={"local_only": True, "red_alerts_auto_share": False},
        thresholds={
            "tlx_p50": mental.GRIER["p50"],
            "tlx_p90": mental.GRIER["p90"],
            "tlx_underload": mental.TLX_UNDERLOAD,
            "cda_green": mental.CDA_GREEN,
            "cda_yellow": mental.CDA_YELLOW,
            "pvt_z_yellow": mental.PVT_Z_YELLOW,
            "pvt_z_red": mental.PVT_Z_RED,
        },
        warnings=[],
    )
