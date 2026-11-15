"""Motor de salud mental: NASA-TLX, CDA, sueño y PVT-B.

Funciones puras. Los datos se guardan como insumos; las curvas y semáforos se
recalculan al leer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import mean, median, stdev

DIMENSIONS = ("MD", "PD", "TD", "OP", "EF", "FR")

PAIRS: tuple[tuple[str, str], ...] = (
    ("MD", "PD"),
    ("MD", "TD"),
    ("MD", "OP"),
    ("MD", "EF"),
    ("MD", "FR"),
    ("PD", "TD"),
    ("PD", "OP"),
    ("PD", "EF"),
    ("PD", "FR"),
    ("TD", "OP"),
    ("TD", "EF"),
    ("TD", "FR"),
    ("OP", "EF"),
    ("OP", "FR"),
    ("EF", "FR"),
)
PAIR_SET = {frozenset(pair) for pair in PAIRS}

TLX_STEP = 5
TLX_BASE_N = 5
TLX_SIGMA_MIN = 5.0
TLX_EWMA_LAMBDA = 0.3
TLX_Z_WARN = 1.0
TLX_Z_RED = 2.0
TLX_EWMA_WARN = 2.0
TLX_EWMA_RED = 3.0
TLX_ABS_WARN = 68.0
TLX_UNDERLOAD = 26.08
GRIER = {"min": 6.21, "p10": 26.08, "p50": 49.93, "p90": 68.00, "max": 88.50}

COLOR_GREEN = 1
COLOR_YELLOW = 2
COLOR_RED = 3

CDA_ITEMS: tuple[tuple[str, str], ...] = (
    ("animo", "+"),
    ("energia", "+"),
    ("motivacion", "+"),
    ("tension", "-"),
    ("tristeza", "-"),
    ("irritabilidad", "-"),
    ("estres", "-"),
    ("fatiga_mental", "-"),
    ("sueno", "+"),
    ("conexion", "+"),
)
CDA_BASE_MIN = 7
CDA_BASE_DAYS = 14
CDA_SIGMA_MIN = 5.0
CDA_WINDOW = 7
CDA_GREEN = 60.0
CDA_YELLOW = 40.0

SLEEP_LATENCY_CHOICES = (5, 10, 15, 20, 30, 45, 60, 90)
DREAMS = ("none", "neutral", "vivid", "nightmare")
PVT_LAPSE_MS = 355.0
PVT_FALSE_START_MS = 100.0
PVT_SIGMA_MIN = 0.209
PVT_Z_YELLOW = -1.0
PVT_Z_RED = -2.0


@dataclass(frozen=True)
class TlxResult:
    ratings: dict[str, int]
    counts: dict[str, int]
    weights: dict[str, float]
    contributions: dict[str, float]
    tlx: float
    rtlx: float
    dominant: str


@dataclass(frozen=True)
class TlxPoint:
    index: int
    taken_at: datetime
    tlx: float
    rtlx: float
    dominant: str
    color: int
    phase: str
    z: float | None
    ewma: float | None
    se: float | None
    limit_warn: float | None
    limit_action: float | None
    underload: bool


@dataclass(frozen=True)
class CdaScore:
    adjusted: dict[str, int]
    iad: float
    positive: float
    negative: float
    stress_fatigue: float
    sleep: float
    connection: float


@dataclass(frozen=True)
class CdaPoint:
    day: date
    iad: float
    color: int
    phase: str
    mm7: float | None
    z: float | None
    flags: tuple[str, ...]


@dataclass(frozen=True)
class NightMetrics:
    tib_min: float
    tst_min: float
    efficiency: float
    midpoint_at: datetime


def score_tlx(
    ratings: dict[str, int],
    comparisons: list[dict],
) -> TlxResult:
    missing = [dimension for dimension in DIMENSIONS if dimension not in ratings]
    if missing:
        raise ValueError(f"missing TLX dimensions: {', '.join(missing)}")
    for dimension in DIMENSIONS:
        value = int(ratings[dimension])
        if value < 0 or value > 100 or value % TLX_STEP != 0:
            raise ValueError(f"rating out of range or not step 5: {dimension}")

    if len(comparisons) != 15:
        raise ValueError("exactly 15 comparisons are required")

    counts = {dimension: 0 for dimension in DIMENSIONS}
    seen: set[frozenset[str]] = set()
    for item in comparisons:
        pair = item.get("pair") or []
        choice = item.get("choice")
        if len(pair) != 2:
            raise ValueError("each comparison needs a pair of two dimensions")
        pair_set = frozenset(pair)
        if pair_set not in PAIR_SET or len(pair_set) != 2:
            raise ValueError("comparison pair is not part of the NASA-TLX set")
        if pair_set in seen:
            raise ValueError("comparison pair repeated")
        if choice not in pair:
            raise ValueError("choice must be one of the pair dimensions")
        seen.add(pair_set)
        counts[choice] += 1

    if sum(counts.values()) != 15:
        raise ValueError("comparisons must sum exactly 15")

    weights = {dimension: counts[dimension] / 15.0 for dimension in DIMENSIONS}
    contributions = {
        dimension: int(ratings[dimension]) * counts[dimension] / 15.0 for dimension in DIMENSIONS
    }
    tlx = sum(contributions.values())
    rtlx = mean(int(ratings[dimension]) for dimension in DIMENSIONS)
    dominant = max(DIMENSIONS, key=lambda dimension: contributions[dimension])

    return TlxResult(
        ratings={dimension: int(ratings[dimension]) for dimension in DIMENSIONS},
        counts=counts,
        weights=weights,
        contributions=contributions,
        tlx=tlx,
        rtlx=rtlx,
        dominant=dominant,
    )


def _level_from_levels(*levels: int) -> int:
    return max(levels)


def evaluate_tlx_series(
    sessions: list[tuple[datetime, float, float, str]],
) -> list[TlxPoint]:
    """Serie ordenada de sesiones TLX (fecha, TLX, RTLX, dominante)."""
    ordered = sorted(sessions, key=lambda item: item[0])
    values = [item[1] for item in ordered]
    points: list[TlxPoint] = []
    baseline_mu = baseline_sigma = 0.0
    if len(values) >= TLX_BASE_N:
        baseline_mu = mean(values[:TLX_BASE_N])
        baseline_sigma = max(stdev(values[:TLX_BASE_N]), TLX_SIGMA_MIN)

    ewma = baseline_mu
    for index, (taken_at, tlx, rtlx, dominant) in enumerate(ordered, start=1):
        underload = tlx < TLX_UNDERLOAD
        if index <= TLX_BASE_N:
            if tlx <= GRIER["p50"]:
                color = COLOR_GREEN
            elif tlx <= GRIER["p90"]:
                color = COLOR_YELLOW
            else:
                color = COLOR_RED
            points.append(
                TlxPoint(
                    index=index,
                    taken_at=taken_at,
                    tlx=round(tlx, 2),
                    rtlx=round(rtlx, 2),
                    dominant=dominant,
                    color=color,
                    phase="calibration",
                    z=None,
                    ewma=None,
                    se=None,
                    limit_warn=None,
                    limit_action=None,
                    underload=underload,
                )
            )
            continue

        step = index - TLX_BASE_N
        ewma = TLX_EWMA_LAMBDA * tlx + (1 - TLX_EWMA_LAMBDA) * ewma
        se = baseline_sigma * math.sqrt(
            (TLX_EWMA_LAMBDA / (2 - TLX_EWMA_LAMBDA)) * (1 - (1 - TLX_EWMA_LAMBDA) ** (2 * step))
        )
        z = (tlx - baseline_mu) / baseline_sigma
        limit_warn = baseline_mu + TLX_EWMA_WARN * se
        limit_action = baseline_mu + TLX_EWMA_RED * se

        z_level = 0 if z < TLX_Z_WARN else (1 if z < TLX_Z_RED else 2)
        ewma_level = 0 if ewma <= limit_warn else (1 if ewma <= limit_action else 2)
        absolute_level = 1 if tlx > TLX_ABS_WARN else 0
        level = _level_from_levels(z_level, ewma_level, absolute_level)

        points.append(
            TlxPoint(
                index=index,
                taken_at=taken_at,
                tlx=round(tlx, 2),
                rtlx=round(rtlx, 2),
                dominant=dominant,
                color=COLOR_GREEN + level,
                phase="baseline",
                z=round(z, 2),
                ewma=round(ewma, 2),
                se=round(se, 3),
                limit_warn=round(limit_warn, 2),
                limit_action=round(limit_action, 2),
                underload=underload,
            )
        )
    return points


def score_cda(values: dict[str, int]) -> CdaScore:
    for key, _ in CDA_ITEMS:
        if key not in values:
            raise ValueError(f"missing CDA item: {key}")
        value = int(values[key])
        if value < 0 or value > 10:
            raise ValueError(f"CDA item out of range: {key}")

    adjusted = {
        key: (int(values[key]) if direction == "+" else 10 - int(values[key]))
        for key, direction in CDA_ITEMS
    }
    iad = 10.0 * mean(adjusted.values())

    positive = 10.0 * mean([values["animo"], values["energia"], values["motivacion"]])
    negative = 10.0 * mean([values["tension"], values["tristeza"], values["irritabilidad"]])
    stress_fatigue = 10.0 * mean([values["estres"], values["fatiga_mental"]])
    sleep = 10.0 * float(values["sueno"])
    connection = 10.0 * float(values["conexion"])

    return CdaScore(
        adjusted=adjusted,
        iad=iad,
        positive=positive,
        negative=negative,
        stress_fatigue=stress_fatigue,
        sleep=sleep,
        connection=connection,
    )


def evaluate_cda_series(days: list[tuple[date, float]]) -> list[CdaPoint]:
    ordered = sorted(days, key=lambda item: item[0])
    total = len(ordered)
    points: list[CdaPoint] = []

    if total < CDA_BASE_DAYS:
        for day, iad in ordered:
            color = (
                COLOR_GREEN
                if iad >= CDA_GREEN
                else (COLOR_YELLOW if iad >= CDA_YELLOW else COLOR_RED)
            )
            points.append(
                CdaPoint(
                    day=day,
                    iad=round(iad, 2),
                    color=color,
                    phase="provisional",
                    mm7=None,
                    z=None,
                    flags=(),
                )
            )
        return points

    baseline = [value for _, value in ordered[:CDA_BASE_DAYS]]
    mu = mean(baseline)
    sigma = max(stdev(baseline), CDA_SIGMA_MIN)
    yellow_streak = 0

    for index, (day, iad) in enumerate(ordered):
        if index < CDA_BASE_DAYS:
            color = (
                COLOR_GREEN
                if iad >= CDA_GREEN
                else (COLOR_YELLOW if iad >= CDA_YELLOW else COLOR_RED)
            )
            points.append(
                CdaPoint(
                    day=day,
                    iad=round(iad, 2),
                    color=color,
                    phase="provisional",
                    mm7=None,
                    z=None,
                    flags=(),
                )
            )
            continue

        window = [value for _, value in ordered[max(0, index - CDA_WINDOW + 1) : index + 1]]
        mm7 = mean(window)
        z = (iad - mu) / sigma
        flags: list[str] = []
        red = False
        yellow = False

        if mm7 <= mu - 2 * sigma:
            red = True
            flags.append("mm7_low")
        elif mm7 <= mu - sigma:
            yellow = True
            flags.append("mm7_watch")
        if z <= -2:
            yellow = True
            flags.append("z_low")
        if iad < CDA_YELLOW:
            yellow = True
            flags.append("iad_low")
        gap = (day - ordered[index - 1][0]).days
        if gap >= 3:
            yellow = True
            flags.append("gap")

        recent_red_z = sum(
            1 for _, value in ordered[max(0, index - 2) : index + 1] if (value - mu) / sigma <= -2
        )
        if recent_red_z >= 3:
            red = True
            flags.append("z_red_streak")

        if red:
            color = COLOR_RED
            yellow_streak = 0
        elif yellow:
            color = COLOR_YELLOW
            yellow_streak += 1
            if yellow_streak >= 7:
                color = COLOR_RED
                flags.append("yellow_streak")
        else:
            color = COLOR_GREEN
            yellow_streak = 0

        points.append(
            CdaPoint(
                day=day,
                iad=round(iad, 2),
                color=color,
                phase="baseline",
                mm7=round(mm7, 2),
                z=round(z, 2),
                flags=tuple(flags),
            )
        )
    return points


def night_metrics(
    entry_at: datetime,
    latency_min: int,
    waso_min: int,
    final_wake_at: datetime,
    exit_at: datetime,
) -> NightMetrics:
    tib = (exit_at - entry_at).total_seconds() / 60.0
    if tib <= 0:
        raise ValueError("exit must be after entry")
    sleep_start = entry_at + timedelta(minutes=latency_min)
    tst = (final_wake_at - sleep_start).total_seconds() / 60.0 - waso_min
    tst = max(0.0, tst)
    efficiency = 100.0 * tst / tib if tib > 0 else 0.0
    midpoint = sleep_start + (final_wake_at - sleep_start) / 2
    return NightMetrics(
        tib_min=round(tib, 2),
        tst_min=round(tst, 2),
        efficiency=round(efficiency, 2),
        midpoint_at=midpoint,
    )


def sri(nights: list[tuple[datetime, datetime]]) -> float | None:
    """Índice de Regularidad del Sueño a partir de (inicio, fin) por noche."""
    if len(nights) < 5:
        return None
    ordered = sorted(nights, key=lambda item: item[0])

    def asleep(start: datetime, end: datetime, minute: int) -> bool:
        start_minute = start.hour * 60 + start.minute
        base = start.date() if minute >= start_minute else end.date()
        moment = datetime.combine(base, datetime.min.time()) + timedelta(minutes=minute)
        return start <= moment < end

    matches = 0
    for (start_a, end_a), (start_b, end_b) in zip(ordered, ordered[1:], strict=False):
        for minute in range(1440):
            if asleep(start_a, end_a, minute) == asleep(start_b, end_b, minute):
                matches += 1
    return -100.0 + 200.0 * matches / (1440.0 * (len(ordered) - 1))


def sleep_debt(nights: list[tuple[date, float]], need_hours: float) -> float:
    need = need_hours * 60.0
    return sum(max(0.0, need - tst) for _, tst in nights[-7:])


def suggest_window(
    profile_minutes: int,
    se7: float | None,
    need_hours: float,
    blocked: bool = False,
) -> int:
    if blocked or se7 is None:
        return profile_minutes
    if se7 < 85:
        return max(360, profile_minutes - 15)
    if se7 > 90:
        return min(int(need_hours * 60) + 30, profile_minutes + 15)
    return profile_minutes


def pvt_metrics(trials: list[int], false_starts: int = 0) -> dict[str, float | int]:
    valid = [int(rt) for rt in trials if int(rt) >= PVT_FALSE_START_MS]
    false = int(false_starts) + sum(1 for rt in trials if int(rt) < PVT_FALSE_START_MS)
    lapses = sum(1 for rt in valid if rt >= PVT_LAPSE_MS)
    speeds = [1000.0 / rt for rt in valid]
    speed = mean(speeds) if speeds else 0.0
    mean_rt = mean(valid) if valid else 0.0
    return {
        "valid_count": len(valid),
        "lapses": lapses,
        "false_starts": false,
        "mean_rt_ms": round(mean_rt, 2),
        "speed": round(speed, 3),
    }


def pvt_alert(speed: float, prior_speeds: list[float]) -> tuple[int | None, float | None]:
    if len(prior_speeds) < 5:
        return None, None
    mu = mean(prior_speeds)
    sigma = max(stdev(prior_speeds), PVT_SIGMA_MIN)
    z = (speed - mu) / sigma
    if z > PVT_Z_YELLOW:
        color = COLOR_GREEN
    elif z > PVT_Z_RED:
        color = COLOR_YELLOW
    else:
        color = COLOR_RED
    return color, round(z, 2)


def prescription_ids(
    *,
    se7: float | None,
    last_cause: str | None,
    inertia: int | None,
    dreams: str | None,
    environmental: list[str] | None,
    pvt_color: int | None,
    debt_hours: float | None,
    midpoint_shift_min: float | None,
    subjective_alertness: int | None,
    pvt_z: float | None,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    def add(identifier: str, severity: int) -> None:
        items.append({"id": identifier, "severity": severity})

    if se7 is not None and se7 < 85:
        add("R1", 1)
    if last_cause == "A":
        add("R2", 1)
    if last_cause == "B":
        add("R3", 1)
    if inertia is not None and inertia >= 7:
        add("R4", 1)
    if dreams == "nightmare":
        add("R5", 2)
    if pvt_color == 2:
        add("R6", 2)
    elif pvt_color == 3:
        add("R6", 3)
    if debt_hours is not None and debt_hours >= 7:
        add("R7", 2)
    if midpoint_shift_min is not None and midpoint_shift_min >= 120:
        add("R8", 1)
    if environmental and any(item != "nothing" for item in environmental):
        add("R9", 2)
    if (
        subjective_alertness is not None
        and subjective_alertness >= 7
        and pvt_z is not None
        and pvt_z <= -1
    ):
        add("R10", 3)
    return items


@dataclass(frozen=True)
class SleepNightInput:
    day: date
    tst_min: float
    efficiency: float
    midpoint_at: datetime
    inertia: int
    environmental: tuple[str, ...]


@dataclass(frozen=True)
class SleepPoint:
    day: date
    tst_hours: float
    efficiency: float
    color: int
    flags: tuple[str, ...]
    debt_hours: float
    se7: float | None
    midpoint_shift_min: float | None
    excluded: bool


def evaluate_sleep_series(
    nights: list[SleepNightInput],
    need_hours: float,
) -> list[SleepPoint]:
    ordered = sorted(nights, key=lambda item: item.day)
    points: list[SleepPoint] = []

    for index, night in enumerate(ordered):
        flags: list[str] = []
        color = COLOR_GREEN

        if night.tst_min < 300:
            color = COLOR_RED
            flags.append("tst_critical")
        elif night.tst_min < 360:
            color = max(color, COLOR_YELLOW)
            flags.append("tst_low")

        debt = sleep_debt([(item.day, item.tst_min) for item in ordered[: index + 1]], need_hours)
        debt_hours = round(debt / 60.0, 2)
        if debt_hours >= 14:
            color = COLOR_RED
            flags.append("debt_critical")
        elif debt_hours >= 7:
            color = max(color, COLOR_YELLOW)
            flags.append("debt_watch")

        window = ordered[max(0, index - 6) : index + 1]
        se7 = mean(item.efficiency for item in window) if len(window) >= 7 else None
        if se7 is not None and se7 < 85:
            color = max(color, COLOR_YELLOW)
            flags.append("se7_low")

        if index >= 3:
            previous = ordered[:index]
            values = [item.tst_min for item in previous]
            mu = mean(values)
            sigma = max(stdev(values), 30.0)
            recent = mean(item.tst_min for item in ordered[max(0, index - 2) : index + 1])
            z = (recent - mu) / sigma
            if z <= -2:
                color = COLOR_RED
                flags.append("trend_critical")
            elif z <= -1:
                color = max(color, COLOR_YELLOW)
                flags.append("trend_watch")

        midpoint_shift = None
        if index >= 2:
            previous_midpoints = [item.midpoint_at for item in ordered[max(0, index - 7) : index]]
            anchor = min(previous_midpoints)
            base = anchor + timedelta(
                minutes=median(
                    (moment - anchor).total_seconds() / 60.0 for moment in previous_midpoints
                )
            )
            shift = abs((night.midpoint_at - base).total_seconds()) / 60.0
            midpoint_shift = round(shift, 1)
            if shift >= 120:
                color = max(color, COLOR_YELLOW)
                flags.append("midpoint_shift")

        excluded = night.inertia >= 7 and any(item != "nothing" for item in night.environmental)
        if excluded:
            flags.append("environmental_excluded")

        points.append(
            SleepPoint(
                day=night.day,
                tst_hours=round(night.tst_min / 60.0, 2),
                efficiency=night.efficiency,
                color=color,
                flags=tuple(flags),
                debt_hours=debt_hours,
                se7=None if se7 is None else round(se7, 2),
                midpoint_shift_min=midpoint_shift,
                excluded=excluded,
            )
        )
    return points


def worst_color(*colors: int | None) -> int | None:
    present = [color for color in colors if color is not None]
    return max(present) if present else None
