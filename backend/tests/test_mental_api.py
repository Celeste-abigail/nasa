from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.domain import mental
from app.domain.models import CdaDay, PvtTest, SleepNight, SleepProfile, TlxSession
from app.infrastructure.database import get_engine
from app.main import app

API = "/api/v1"

CHOICES = ["MD", "MD", "OP", "EF", "MD", "PD", "OP", "PD", "PD", "OP", "EF", "FR", "OP", "FR", "EF"]
RATINGS = {"MD": 75, "PD": 65, "TD": 65, "OP": 75, "EF": 70, "FR": 65}
CDA = {
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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_mental():
    with Session(get_engine()) as session:
        session.exec(delete(TlxSession))
        session.exec(delete(CdaDay))
        session.exec(delete(SleepNight))
        session.exec(delete(SleepProfile))
        session.exec(delete(PvtTest))
        session.commit()
    yield


def _create(client: TestClient, code: str) -> None:
    response = client.post(
        f"{API}/astronauts",
        json={
            "code": code,
            "name": "Mental test",
            "sex": "male",
            "birth_date": "1985-04-12",
        },
    )
    assert response.status_code in (201, 409), response.text


def _comparisons() -> list[dict]:
    return [
        {"pair": list(pair), "choice": choice}
        for pair, choice in zip(mental.PAIRS, CHOICES, strict=True)
    ]


def test_tlx_flow(client: TestClient) -> None:
    _create(client, "MEN-1")
    response = client.post(
        f"{API}/astronauts/MEN-1/mental/tlx",
        json={
            "task_description": "Revisión de regulador térmico",
            "task_category": "EVA",
            "duration_min": 120,
            "ratings": RATINGS,
            "comparisons": _comparisons(),
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tlx"] == pytest.approx(70.67, abs=0.01)
    assert body["rtlx"] == pytest.approx(69.17, abs=0.01)
    assert body["dominant"] == "OP"
    assert body["counts"]["TD"] == 0

    assessment = client.get(f"{API}/astronauts/MEN-1/mental").json()
    assert len(assessment["tlx_points"]) == 1
    assert assessment["tlx_points"][0]["color"] == 3
    assert assessment["current_tlx"]["tlx"] == pytest.approx(70.67, abs=0.01)


def test_cda_flow(client: TestClient) -> None:
    _create(client, "MEN-2")
    response = client.put(f"{API}/astronauts/MEN-2/mental/cda/2026-11-01", json={"items": CDA})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["iad"] == pytest.approx(63.0)
    assert body["positive"] == pytest.approx(66.67, abs=0.01)
    assert body["negative"] == pytest.approx(30.0)
    assert body["color"] == 1


def test_sleep_and_profile_flow(client: TestClient) -> None:
    _create(client, "MEN-3")
    profile = client.put(
        f"{API}/astronauts/MEN-3/mental/sleep/profile",
        json={
            "need_hours": 7.5,
            "scheduled_wake": "06:00",
            "window_minutes": 450,
            "blocked": False,
        },
    )
    assert profile.status_code == 200, profile.text

    night = client.put(
        f"{API}/astronauts/MEN-3/mental/sleep/2026-11-02",
        json={
            "day": "2026-11-02",
            "entry_at": "2026-11-01T22:30:00",
            "latency_min": 25,
            "awakenings": 2,
            "waso_min": 40,
            "cause_group": "A",
            "cause_detail": "work",
            "final_wake_at": "2026-11-02T05:50:00",
            "exit_at": "2026-11-02T06:10:00",
            "quality": 6,
            "inertia": 8,
            "dreams": "nightmare",
            "environmental": ["nothing"],
            "nap_min": 0,
        },
    )
    assert night.status_code == 200, night.text
    body = night.json()
    assert body["tib_min"] == pytest.approx(460)
    assert body["tst_min"] == pytest.approx(375)
    assert body["efficiency"] == pytest.approx(81.52, abs=0.01)
    assert body["color"] == 1
    assert body["flags"] == []


def test_pvt_requires_baseline_for_color(client: TestClient) -> None:
    _create(client, "MEN-4")
    trials = [245, 260, 231, 298, 410, 252, 240, 367, 229, 275, 90, 255]
    first = client.post(
        f"{API}/astronauts/MEN-4/mental/pvt",
        json={"mode": 60, "trials": trials, "subjective_alertness": 8},
    )
    assert first.status_code == 201, first.text
    assert first.json()["color"] is None
    assert first.json()["speed"] == pytest.approx(3.712, abs=0.001)
    assert first.json()["discrepancy"] is False

    for _ in range(5):
        response = client.post(
            f"{API}/astronauts/MEN-4/mental/pvt",
            json={
                "mode": 60,
                "trials": [240, 245, 250, 235, 255],
                "subjective_alertness": 6,
            },
        )
        assert response.status_code == 201, response.text

    assessment = client.get(f"{API}/astronauts/MEN-4/mental").json()
    assert len(assessment["pvt_tests"]) == 6
    assert assessment["current_pvt"]["z"] is not None


def test_assessment_contains_prescriptions(client: TestClient) -> None:
    _create(client, "MEN-5")
    client.post(
        f"{API}/astronauts/MEN-5/mental/tlx",
        json={
            "task_description": "Tarea de prueba",
            "task_category": "Robótica",
            "ratings": RATINGS,
            "comparisons": _comparisons(),
        },
    )
    client.put(f"{API}/astronauts/MEN-5/mental/cda/2026-11-14", json={"items": CDA})
    client.put(
        f"{API}/astronauts/MEN-5/mental/sleep/2026-11-14",
        json={
            "day": "2026-11-14",
            "entry_at": "2026-11-13T22:30:00",
            "latency_min": 25,
            "awakenings": 2,
            "waso_min": 40,
            "cause_group": "A",
            "final_wake_at": "2026-11-14T05:50:00",
            "exit_at": "2026-11-14T06:10:00",
            "quality": 6,
            "inertia": 8,
            "dreams": "nightmare",
            "environmental": ["nothing"],
        },
    )
    assessment = client.get(f"{API}/astronauts/MEN-5/mental").json()
    ids = {item["id"] for item in assessment["prescriptions"]}
    assert {"R2", "R4", "R5"} <= ids
    assert assessment["global_color"] == 3
    assert assessment["sleep_profile"]["need_hours"] == 7.5
    assert assessment["privacy"]["red_alerts_auto_share"] is False
    assert assessment["adherence"]["cda_days"] == 1


def test_validation_errors(client: TestClient) -> None:
    _create(client, "MEN-6")

    bad_tlx = client.post(
        f"{API}/astronauts/MEN-6/mental/tlx",
        json={
            "task_description": "Tarea",
            "task_category": "EVA",
            "ratings": RATINGS,
            "comparisons": _comparisons()[:-1],
        },
    )
    assert bad_tlx.status_code == 422

    bad_cda = client.put(
        f"{API}/astronauts/MEN-6/mental/cda/2026-11-01",
        json={"items": {**CDA, "animo": 11}},
    )
    assert bad_cda.status_code == 422

    bad_sleep = client.put(
        f"{API}/astronauts/MEN-6/mental/sleep/2026-11-02",
        json={
            "day": "2026-11-02",
            "entry_at": "2026-11-02T06:10:00",
            "latency_min": 25,
            "awakenings": 0,
            "waso_min": 0,
            "final_wake_at": "2026-11-02T05:50:00",
            "exit_at": "2026-11-01T22:30:00",
            "quality": 6,
            "inertia": 2,
            "dreams": "none",
            "environmental": [],
        },
    )
    assert bad_sleep.status_code == 422

    bad_pvt = client.post(f"{API}/astronauts/MEN-6/mental/pvt", json={"mode": 60, "trials": []})
    assert bad_pvt.status_code == 422
