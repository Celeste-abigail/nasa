from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.domain.models import MentalDay, MentalTask
from app.infrastructure.database import get_engine
from app.main import app

API = "/api/v1"

RATINGS = {"MD": 60, "PD": 50, "TD": 40, "OP": 30, "EF": 55, "FR": 35}
MOOD = {
    "m1_sleep": 8,
    "m2_vigor": 8,
    "m3_calm": 7,
    "m4_cohesion": 9,
    "m5_tension": 2,
    "m6_irrit": 1,
    "m7_dysphoria": 1,
    "m8_somatic": 2,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_mental():
    with Session(get_engine()) as session:
        session.exec(delete(MentalTask))
        session.exec(delete(MentalDay))
        session.commit()
    yield


def _create_astronaut(client: TestClient, code: str) -> None:
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


def _day_payload(**overrides):
    payload = {
        "mission_day": 12,
        "mood": dict(MOOD),
        "tasks": [
            {
                "task_ref": "TSK-1",
                "category": "EVA",
                "name": "Revision",
                "duration_min": 120,
                "eval_mode": "RAW_FAST",
                "ratings": dict(RATINGS),
            }
        ],
        "acute_24h_dose_mgy": 20.0,
    }
    payload.update(overrides)
    return payload


def test_upsert_and_get(client: TestClient) -> None:
    _create_astronaut(client, "M-01")
    response = client.put(f"{API}/astronauts/M-01/mental/2026-11-10", json=_day_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current"]["day"] == "2026-11-10"
    assert body["current"]["wl_day"] == pytest.approx(45.0)
    assert body["current"]["dmrs"] == pytest.approx(82.5, abs=0.1)
    assert body["current"]["zone"] == "green"
    assert body["current"]["color"] == 1
    assert len(body["current"]["tasks"]) == 1
    assert body["current"]["tasks"][0]["overall"] == pytest.approx(45.0)

    fetched = client.get(f"{API}/astronauts/M-01/mental").json()
    assert len(fetched["days"]) == 1
    assert fetched["thresholds"]["ali_green_max"] == 45.0


def test_upsert_replaces_tasks_and_recomputes(client: TestClient) -> None:
    _create_astronaut(client, "M-02")
    client.put(f"{API}/astronauts/M-02/mental/2026-11-10", json=_day_payload())
    client.put(
        f"{API}/astronauts/M-02/mental/2026-11-10",
        json=_day_payload(
            tasks=[
                {
                    "task_ref": "TSK-1",
                    "category": "EVA",
                    "name": "Revision",
                    "duration_min": 60,
                    "eval_mode": "RAW_FAST",
                    "ratings": dict(RATINGS),
                },
                {
                    "task_ref": "TSK-2",
                    "category": "LAB",
                    "name": "Analisis",
                    "duration_min": 60,
                    "eval_mode": "RAW_FAST",
                    "ratings": {key: 90 for key in RATINGS},
                },
            ]
        ),
    )
    body = client.get(f"{API}/astronauts/M-02/mental").json()
    assert len(body["days"]) == 1
    assert len(body["current"]["tasks"]) == 2
    assert body["current"]["wl_day"] == pytest.approx(67.5)


def test_weighted_tlx_requires_tallies(client: TestClient) -> None:
    _create_astronaut(client, "M-03")
    payload = _day_payload(
        tasks=[
            {
                "duration_min": 60,
                "eval_mode": "WEIGHTED_FULL",
                "ratings": dict(RATINGS),
                "tallies": {"MD": 3, "PD": 3, "TD": 3, "OP": 3, "EF": 2, "FR": 1},
            }
        ]
    )
    response = client.put(f"{API}/astronauts/M-03/mental/2026-11-10", json=payload)
    assert response.status_code == 200, response.text

    broken = _day_payload(
        tasks=[
            {
                "duration_min": 60,
                "eval_mode": "WEIGHTED_FULL",
                "ratings": dict(RATINGS),
                "tallies": {"MD": 5, "PD": 5, "TD": 4, "OP": 0, "EF": 0, "FR": 0},
            }
        ]
    )
    bad = client.put(f"{API}/astronauts/M-03/mental/2026-11-11", json=broken)
    assert bad.status_code == 422
    assert "tallies" in bad.json()["detail"].lower()


def test_future_day_is_rejected(client: TestClient) -> None:
    _create_astronaut(client, "M-04")
    response = client.put(f"{API}/astronauts/M-04/mental/2099-01-01", json=_day_payload())
    assert response.status_code == 422
    assert "futuro" in response.json()["detail"].lower()


def test_mood_out_of_range_is_rejected(client: TestClient) -> None:
    _create_astronaut(client, "M-05")
    payload = _day_payload(mood={**MOOD, "m1_sleep": 11})
    response = client.put(f"{API}/astronauts/M-05/mental/2026-11-10", json=payload)
    assert response.status_code == 422


def test_series_accumulates_days(client: TestClient) -> None:
    _create_astronaut(client, "M-06")
    for index, day in enumerate(("2026-11-09", "2026-11-10", "2026-11-11")):
        response = client.put(
            f"{API}/astronauts/M-06/mental/{day}",
            json=_day_payload(mission_day=10 + index),
        )
        assert response.status_code == 200, response.text

    body = client.get(f"{API}/astronauts/M-06/mental").json()
    assert len(body["days"]) == 3
    ewmas = [item["ewma_wl"] for item in body["days"]]
    assert ewmas[0] == pytest.approx(45.0)
    assert ewmas[1] == pytest.approx(45.0)
    assert body["current"]["day"] == "2026-11-11"
