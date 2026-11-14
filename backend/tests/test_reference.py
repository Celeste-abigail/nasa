from __future__ import annotations

from datetime import date

import pytest

from app.domain import reference


def test_age_at_uses_measurement_date() -> None:
    assert reference.age_at(date(1985, 4, 12), date(2026, 4, 11)) == 40
    assert reference.age_at(date(1985, 4, 12), date(2026, 4, 12)) == 41
    assert reference.age_at(None, date(2026, 4, 12)) is None


def test_reference_has_twelve_groups() -> None:
    assert len(reference.groups()) == 12


@pytest.mark.parametrize(
    ("sex", "age", "band", "clamped"),
    [
        ("male", 20, "20-29", False),
        ("male", 29, "20-29", False),
        ("male", 30, "30-39", False),
        ("female", 45, "40-49", False),
        ("female", 74, "70-74", False),
        ("female", 75, "70-74", True),
        ("male", 18, "20-29", True),
    ],
)
def test_match_selects_band(sex, age, band, clamped) -> None:
    matched = reference.match(sex, age)
    assert matched is not None
    assert matched.group.age_band == band
    assert matched.clamped is clamped


def test_match_requires_sex_and_age() -> None:
    assert reference.match(None, 40) is None
    assert reference.match("male", None) is None


def test_young_reference_is_the_twenties_group() -> None:
    matched = reference.match("female", 50)
    assert matched is not None
    assert matched.young.age_band == "20-29"
    assert matched.young.bua_mean == pytest.approx(113.2)


def test_reference_values_match_source_table() -> None:
    matched = reference.match("male", 41)
    assert matched is not None
    assert matched.group.bua_mean == pytest.approx(119.2)
    assert matched.group.bua_sd == pytest.approx(13.9)
    assert matched.group.sos_mean == pytest.approx(1548.7)
    assert matched.group.sos_sd == pytest.approx(40.7)


def test_bua_scores_and_classification() -> None:
    matched = reference.match("male", 41)
    assert matched is not None
    score = reference.evaluate_metric(119.2, matched, "bua")
    assert score.z == pytest.approx(0.0)
    assert score.t == pytest.approx((119.2 - 121.4) / 15.6)
    assert score.status == reference.STATUS_NORMAL


def test_low_bua_is_osteopenia_or_osteoporosis() -> None:
    matched = reference.match("male", 41)
    assert matched is not None
    osteopenia = reference.evaluate_metric(105.0, matched, "bua")
    osteoporosis = reference.evaluate_metric(80.0, matched, "bua")
    assert osteopenia.status == reference.STATUS_OSTEOPENIA
    assert osteoporosis.status == reference.STATUS_OSTEOPOROSIS


@pytest.mark.parametrize(
    ("t", "status"),
    [
        (0.0, reference.STATUS_NORMAL),
        (-0.99, reference.STATUS_NORMAL),
        (-1.0, reference.STATUS_NORMAL),
        (-1.01, reference.STATUS_OSTEOPENIA),
        (-2.49, reference.STATUS_OSTEOPENIA),
        (-2.5, reference.STATUS_OSTEOPOROSIS),
        (None, reference.STATUS_UNKNOWN),
    ],
)
def test_classify_thresholds(t, status) -> None:
    assert reference.classify(t) == status


def test_worst_status_ranks_osteoporosis_highest() -> None:
    assert reference.worst_status("normal", "osteopenia") == "osteopenia"
    assert reference.worst_status("osteopenia", "osteoporosis") == "osteoporosis"
    assert reference.worst_status("unknown", "normal") == "normal"


def test_sos_uses_uv_metric() -> None:
    matched = reference.match("male", 41)
    assert matched is not None
    score = reference.evaluate_metric(1548.7, matched, "sos")
    assert score.z == pytest.approx(0.0)
    assert score.mean == pytest.approx(1548.7)
