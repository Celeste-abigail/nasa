from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.domain import radiation


def test_reference_matches_generated_file() -> None:
    ref = radiation.reference()
    general = next(
        stratum
        for stratum in ref.strata
        if stratum.region == "all" and stratum.hour is None and stratum.epoch is None
    )
    assert general.n == 1441
    assert general.eq is not None
    assert general.eq.p50 == pytest.approx(0.238, abs=1e-3)
    assert general.eq.p95 == pytest.approx(1.175, abs=1e-3)
    assert general.eq.p99 == pytest.approx(12.881, abs=1e-3)
    assert ref.limits["career_msv"] == 600.0
    assert ref.daily["eq"].insufficient is True


def test_hourly_cells_fall_back_to_general() -> None:
    stratum, fallback = radiation.select_stratum("saa", 10, "eq")
    assert stratum is not None
    assert stratum.region == "all"
    assert fallback is True


def test_instant_classification() -> None:
    ref = radiation.reference()
    general = next(
        stratum
        for stratum in ref.strata
        if stratum.region == "all" and stratum.hour is None and stratum.epoch is None
    )
    assert general.eq is not None

    green = radiation.classify_instant(0.5, general.eq, [])
    yellow = radiation.classify_instant(2.0, general.eq, [])
    single = radiation.classify_instant(20.0, general.eq, [])
    sustained = radiation.classify_instant(20.0, general.eq, [18.0, 19.0])

    assert green.color == radiation.COLOR_GREEN
    assert yellow.color == radiation.COLOR_YELLOW
    assert single.color == radiation.COLOR_YELLOW
    assert single.detail == "above_p99_single"
    assert sustained.color == radiation.COLOR_RED
    assert sustained.detail == "above_p99_sustained"


def test_invalid_and_missing_values() -> None:
    assert radiation.classify_instant(None, None, []).status == radiation.STATUS_INVALID
    assert radiation.classify_instant(0.5, None, []).status == radiation.STATUS_INSUFFICIENT


def test_daily_layer_is_insufficient_without_reference() -> None:
    ref = radiation.reference()
    layer = radiation.classify_daily(0.9, 1.0, ref.daily["eq"])
    assert layer.status == radiation.STATUS_INSUFFICIENT
    assert layer.detail == "no_daily_reference"

    no_coverage = radiation.classify_daily(0.9, 0.0, ref.daily["eq"])
    assert no_coverage.status == radiation.STATUS_INSUFFICIENT


def test_cumulative_fractions() -> None:
    assert radiation.classify_cumulative(0.3, None).color == radiation.COLOR_GREEN
    assert radiation.classify_cumulative(0.6, None).color == radiation.COLOR_YELLOW
    assert radiation.classify_cumulative(None, 0.85).color == radiation.COLOR_RED
    assert radiation.classify_cumulative(None, None).status == radiation.STATUS_INSUFFICIENT


def test_integration_and_gap_cap() -> None:
    start = datetime(2018, 4, 11, 10, 0)
    pairs = [(start, 6.0), (start + timedelta(minutes=10), 6.0)]
    assert radiation.integrate_msv(pairs) == pytest.approx(0.06)

    wide = [(start, 6.0), (start + timedelta(minutes=120), 6.0)]
    assert radiation.integrate_msv(wide) == pytest.approx(0.36)  # tope de 60 min


def test_daily_window_coverage() -> None:
    start = datetime(2018, 4, 11, 0, 0)
    pairs = [
        (start, 1.0),
        (start + timedelta(hours=12), 1.0),
    ]
    total, coverage = radiation.daily_window(pairs, start.date())
    # El integrador limita cada hueco a 60 min (ruido/telemetria).
    assert total == pytest.approx(0.06)
    assert coverage == pytest.approx(0.5)


def test_quality_factor() -> None:
    assert radiation.q_factor(1.8, 1.0) == pytest.approx(1.8)
    assert radiation.q_factor(1.8, None) is None
    assert radiation.q_factor(1.8, 0.0) is None
