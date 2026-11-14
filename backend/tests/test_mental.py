from __future__ import annotations

from datetime import date

import pytest

from app.domain import mental


def mood_values(m1=6, m2=5, m3=6, m4=8, m5=4, m6=3, m7=2, m8=4) -> dict[str, int]:
    return {
        "m1_sleep": m1,
        "m2_vigor": m2,
        "m3_calm": m3,
        "m4_cohesion": m4,
        "m5_tension": m5,
        "m6_irrit": m6,
        "m7_dysphoria": m7,
        "m8_somatic": m8,
    }


def test_tlx_matches_document_example() -> None:
    result = mental.compute_tlx(
        {"MD": 75, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65},
        {"MD": 3, "PD": 3, "TD": 0, "OP": 4, "EF": 3, "FR": 2},
        "WEIGHTED_FULL",
    )
    assert result.overall == pytest.approx(70.6667, abs=1e-3)
    assert sum(result.weights.values()) == pytest.approx(1.0)
    assert result.weights["TD"] == 0.0
    assert result.weights["OP"] == pytest.approx(4 / 15)


def test_tlx_raw_fast_uses_uniform_weights() -> None:
    ratings = {"MD": 50, "PD": 60, "TD": 70, "OP": 80, "EF": 90, "FR": 100}
    result = mental.compute_tlx(ratings, None, "RAW_FAST")
    assert result.overall == pytest.approx(75.0)
    assert all(weight == pytest.approx(1 / 6) for weight in result.weights.values())


@pytest.mark.parametrize(
    "ratings",
    [
        {"MD": 72, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65},
        {"MD": 105, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65},
        {"MD": 75, "PD": 65, "TD": 65, "OP": 75, "EF": 70},
    ],
)
def test_tlx_rejects_invalid_ratings(ratings) -> None:
    with pytest.raises(ValueError):
        mental.compute_tlx(ratings, None, "RAW_FAST")


def test_tlx_weighted_requires_fifteen_tallies() -> None:
    with pytest.raises(ValueError):
        mental.compute_tlx(
            {"MD": 75, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65},
            {"MD": 3, "PD": 3, "TD": 0, "OP": 4, "EF": 3, "FR": 1},
            "WEIGHTED_FULL",
        )


def test_mood_scores_match_document_formula() -> None:
    result = mental.compute_mood(mood_values())
    assert result.pa == pytest.approx(62.5)
    assert result.na == pytest.approx(32.5)
    assert result.dmrs == pytest.approx(64.5)


def test_daily_workload_weights_by_duration() -> None:
    assert mental.daily_workload([(70.0, 120), (30.0, 40)]) == pytest.approx(60.0)
    assert mental.daily_workload([]) == 0.0


def test_ewma_alpha() -> None:
    assert mental.ewma(50.0, 100.0) == pytest.approx(67.5)
    assert mental.ewma(0.0, 10.0, alpha=1.0) == pytest.approx(10.0)


def _series(days: list[dict]) -> list[mental.DayResult]:
    inputs = [
        mental.DayInput(
            day=date(2026, 11, 1 + index),
            mission_day=index + 1,
            mood=item.get("mood", mood_values()),
            wl_day=item["wl"],
            acute_24h_dose_mgy=item.get("acute"),
        )
        for index, item in enumerate(days)
    ]
    return mental.build_series(inputs)


def test_series_applies_sleep_debt_penalty() -> None:
    results = _series(
        [
            {"wl": 50.0, "mood": mood_values(m1=3)},
            {"wl": 50.0, "mood": mood_values(m1=2)},
        ]
    )
    assert results[0].sleep_debt is False
    assert results[1].sleep_debt is True
    assert results[1].ali > results[0].ali


def test_zone_orange_when_mood_below_baseline() -> None:
    results = _series(
        [
            {
                "wl": 50.0,
                "mood": mood_values(m1=5, m2=5, m3=5, m4=5, m5=5, m6=5, m7=5, m8=5),
            }
        ]
    )
    assert results[-1].dmrs == pytest.approx(50.0)
    assert results[-1].zone == "orange"


def test_zone_red_when_mood_is_critical() -> None:
    results = _series([{"wl": 60.0, "mood": mood_values(m7=10, m5=10, m8=10, m6=10)}])
    assert results[-1].zone == "red"


def test_zone_red_when_ali_is_critical() -> None:
    results = _series([{"wl": 100.0, "mood": mood_values()}])
    assert results[-1].ali > 65
    assert results[-1].zone == "red"
    assert "ali_critical" in results[-1].reasons


def test_zone_red_for_acute_radiation() -> None:
    results = _series([{"wl": 50.0, "mood": mood_values(), "acute": 600.0}])
    assert results[-1].acute_radiation is True
    assert results[-1].zone == "red"


def test_zone_yellow_when_compensated_overload() -> None:
    results = _series(
        [
            {
                "wl": 80.0,
                "mood": mood_values(m1=10, m2=10, m3=10, m4=10, m5=0, m6=0, m7=0, m8=0),
            }
        ]
    )
    assert results[-1].zone == "yellow"


def test_zone_green_homeostasis() -> None:
    results = _series(
        [
            {
                "wl": 40.0,
                "mood": mood_values(m1=9, m2=9, m3=9, m4=9, m5=1, m6=1, m7=1, m8=1),
            }
        ]
    )
    assert results[-1].zone == "green"


def test_burnout_rule_red() -> None:
    results = _series(
        [
            {
                "wl": 20.0,
                "mood": mood_values(m1=5, m2=5, m3=5, m4=5, m5=8, m6=8, m7=8, m8=8),
            }
        ]
    )
    assert results[-1].burnout is True
    assert results[-1].zone == "red"
