from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def seeded_astronaut(client: TestClient) -> None:
    response = client.post(
        f"{API}/astronauts",
        json={
            "code": "EXP-1",
            "name": "Export test",
            "sex": "male",
            "birth_date": "1985-04-12",
        },
    )
    assert response.status_code in (201, 409), response.text
    client.post(
        f"{API}/astronauts/EXP-1/measurements",
        json={
            "measured_on": "2026-10-01",
            "site": "calcaneus",
            "bua": 118.0,
            "uv": 1552.0,
            "att": None,
        },
    )
    client.post(
        f"{API}/astronauts/EXP-1/cortisol",
        json={"measured_at": "2026-10-01T07:00:00", "value": 0.5, "unit": "ug_dl"},
    )
    client.put(
        f"{API}/astronauts/EXP-1/mental/2026-10-01",
        json={
            "mission_day": 10,
            "mood": {
                "m1_sleep": 8,
                "m2_vigor": 8,
                "m3_calm": 8,
                "m4_cohesion": 8,
                "m5_tension": 2,
                "m6_irrit": 2,
                "m7_dysphoria": 2,
                "m8_somatic": 2,
            },
            "tasks": [
                {
                    "duration_min": 60,
                    "eval_mode": "RAW_FAST",
                    "ratings": {"MD": 50, "PD": 50, "TD": 50, "OP": 50, "EF": 50, "FR": 50},
                }
            ],
        },
    )


def test_summary_json(client: TestClient) -> None:
    response = client.get(f"{API}/astronauts/EXP-1/export/summary.json?lang=es")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")
    body = response.json()
    assert body["astronaut"]["code"] == "EXP-1"
    assert {section["title"] for section in body["sections"]} >= {
        "Densidad osea (SCAN)",
        "Cortisol salival",
        "Salud mental",
    }
    assert body["disclaimer"]


def test_summary_html(client: TestClient) -> None:
    response = client.get(f"{API}/astronauts/EXP-1/export/summary.html?lang=es")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    text = response.text
    assert "Astro Health Monitor" in text
    assert "EXP-1" in text
    assert "Recomendacion" in text or "Recomendación" in text


def test_summary_pdf(client: TestClient) -> None:
    response = client.get(f"{API}/astronauts/EXP-1/export/summary.pdf?lang=en")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


def test_data_json(client: TestClient) -> None:
    response = client.get(f"{API}/astronauts/EXP-1/export/data.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["astronaut"]["code"] == "EXP-1"
    assert payload["bone"]["current"]["bua"] == pytest.approx(118.0)
    assert payload["cortisol"]["current"]["value_ug_dl"] == pytest.approx(0.5)
    assert len(payload["mental"]["days"]) == 1


def test_data_csv(client: TestClient) -> None:
    response = client.get(f"{API}/astronauts/EXP-1/export/data.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.text.lstrip("\ufeff")
    lines = text.strip().splitlines()
    assert lines[0] == "module,recorded_at,metric,value,unit,flags,notes"
    assert any(line.startswith("bone,2026-10-01,bua,118.0") for line in lines)
    assert any(line.startswith("cortisol,2026-10-01T07:00:00,value") for line in lines)
    assert any(line.startswith("mental,2026-10-01,ali") for line in lines)

    parsed = list(__import__("csv").DictReader(text.splitlines()))
    assert json.dumps(parsed[0])  # el CSV es parseable
