from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app.domain import mental

CHOICES = ["MD", "MD", "OP", "EF", "MD", "PD", "OP", "PD", "PD", "OP", "EF", "FR", "OP", "FR", "EF"]


def comparisons() -> list[dict]:
    return [
        {"pair": list(pair), "choice": choice}
        for pair, choice in zip(mental.PAIRS, CHOICES, strict=True)
    ]


def tlx_series(values: list[float]) -> list[mental.TlxPoint]:
    start = datetime(2026, 1, 1, 12, 0)
    return mental.evaluate_tlx_series(
        [(start + timedelta(days=index), value, value, "MD") for index, value in enumerate(values)]
    )


def test_tlx_matches_document_example() -> None:
    result = mental.score_tlx(
        {"MD": 75, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65},
        comparisons(),
    )
    assert result.counts == {"MD": 3, "PD": 3, "TD": 0, "OP": 4, "EF": 3, "FR": 2}
    assert result.tlx == pytest.approx(70.67, abs=0.01)
    assert result.rtlx == pytest.approx(69.17, abs=0.01)
    assert result.dominant == "OP"
    assert result.contributions["OP"] == pytest.approx(20.0, abs=0.01)


def test_tlx_uniform_ratings() -> None:
    result = mental.score_tlx({key: 50 for key in mental.DIMENSIONS}, comparisons())
    assert result.tlx == pytest.approx(50.0)
    assert result.rtlx == pytest.approx(50.0)


def test_tlx_requires_fifteen_comparisons() -> None:
    with pytest.raises(ValueError):
        mental.score_tlx({key: 50 for key in mental.DIMENSIONS}, comparisons()[:-1])


def test_tlx_rejects_invalid_rating_step() -> None:
    with pytest.raises(ValueError):
        mental.score_tlx({**{key: 50 for key in mental.DIMENSIONS}, "MD": 52}, comparisons())


def test_tlx_calibration_colors() -> None:
    assert tlx_series([70.67])[-1].color == mental.COLOR_RED
    assert tlx_series([49.0])[-1].color == mental.COLOR_GREEN
    assert tlx_series([55.0])[-1].color == mental.COLOR_YELLOW


def test_tlx_personal_baseline_sem2() -> None:
    point = tlx_series([50, 45, 55, 50, 60, 55])[-1]
    assert point.phase == "baseline"
    assert point.z == pytest.approx(0.53, abs=0.01)
    assert point.ewma == pytest.approx(52.90, abs=0.01)
    assert point.limit_warn == pytest.approx(55.42, abs=0.01)
    assert point.color == mental.COLOR_GREEN


def test_tlx_personal_baseline_sem3() -> None:
    point = tlx_series([50, 45, 55, 50, 60, 55, 48, 52, 58, 50, 62, 66])[-1]
    assert point.z == pytest.approx(2.46, abs=0.01)
    assert point.ewma == pytest.approx(58.53, abs=0.01)
    assert point.color == mental.COLOR_RED


def test_tlx_underload() -> None:
    assert tlx_series([20.0])[-1].underload is True


CDA_VALUES = {
    "animo": 7,
    "energia": 6,
    "motivacion": 7,
    "tension": 3,
    "tristeza": 2,
    "irritabilidad": 4,
    "estres": 5,
    "fatiga_mental": 6,
    "sueno": 5,
    "conexion": 8,
}


def test_cda_scores_match_document() -> None:
    score = mental.score_cda(CDA_VALUES)
    assert score.iad == pytest.approx(63.0)
    assert score.positive == pytest.approx(66.67, abs=0.01)
    assert score.negative == pytest.approx(30.0)
    assert score.stress_fatigue == pytest.approx(55.0)
    assert score.sleep == pytest.approx(50.0)
    assert score.connection == pytest.approx(80.0)


def test_cda_perfect_day() -> None:
    values = {key: (10 if direction == "+" else 0) for key, direction in mental.CDA_ITEMS}
    assert mental.score_cda(values).iad == pytest.approx(100.0)


def test_cda_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        mental.score_cda({**CDA_VALUES, "animo": 11})


def test_night_metrics_match_document() -> None:
    metrics = mental.night_metrics(
        datetime(2026, 11, 1, 22, 30),
        25,
        40,
        datetime(2026, 11, 2, 5, 50),
        datetime(2026, 11, 2, 6, 10),
    )
    assert metrics.tib_min == pytest.approx(460)
    assert metrics.tst_min == pytest.approx(375)
    assert metrics.efficiency == pytest.approx(81.52, abs=0.01)
    assert metrics.midpoint_at.strftime("%H:%M:%S") == "02:22:30"


def _regular_nights() -> list[tuple[datetime, datetime]]:
    return [
        (datetime(2026, 11, 1 + index, 22, 55), datetime(2026, 11, 2 + index, 5, 50))
        for index in range(7)
    ]


def test_sri_perfect_regularity() -> None:
    assert mental.sri(_regular_nights()) == pytest.approx(100.0)


def test_sri_shifted_night() -> None:
    nights = _regular_nights()
    nights[3] = (datetime(2026, 11, 4, 1, 55), datetime(2026, 11, 4, 8, 50))
    assert mental.sri(nights) == pytest.approx(83.33, abs=0.01)


def test_sleep_debt_and_window() -> None:
    values = [375, 400, 420, 350, 390, 410, 380]
    nights = [(date(2026, 11, 1 + index), value) for index, value in enumerate(values)]
    debt = mental.sleep_debt(nights, 7.5)
    assert debt / 60.0 == pytest.approx(7.08, abs=0.01)

    assert mental.suggest_window(450, 81.5, 7.5) == 435
    assert mental.suggest_window(450, 92.0, 7.5) == 465
    assert mental.suggest_window(450, 87.0, 7.5) == 450
    assert mental.suggest_window(360, 70.0, 7.5) == 360
    assert mental.suggest_window(450, 70.0, 7.5, blocked=True) == 450


def test_sleep_series_flags_debt() -> None:
    values = [375, 400, 420, 350, 390, 410, 380]
    inputs = [
        mental.SleepNightInput(
            day=date(2026, 11, 1 + index),
            tst_min=value,
            efficiency=81.5,
            midpoint_at=datetime(2026, 11, 2 + index, 2, 22),
            inertia=2,
            environmental=(),
        )
        for index, value in enumerate(values)
    ]
    points = mental.evaluate_sleep_series(inputs, 7.5)
    assert points[-1].debt_hours == pytest.approx(7.08, abs=0.01)
    assert "debt_watch" in points[-1].flags


def test_pvt_metrics_match_document() -> None:
    trials = [245, 260, 231, 298, 410, 252, 240, 367, 229, 275, 90, 255]
    metrics = mental.pvt_metrics(trials)
    assert metrics["valid_count"] == 11
    assert metrics["lapses"] == 2
    assert metrics["false_starts"] == 1
    assert metrics["mean_rt_ms"] == pytest.approx(278.36, abs=0.01)
    assert metrics["speed"] == pytest.approx(3.712, abs=0.001)


def test_pvt_alert_matches_document() -> None:
    prior = [4.10, 4.25, 4.05, 4.20, 4.15, 4.30]
    color, z = mental.pvt_alert(3.712, prior)
    assert z == pytest.approx(-2.22, abs=0.01)
    assert color == mental.COLOR_RED
