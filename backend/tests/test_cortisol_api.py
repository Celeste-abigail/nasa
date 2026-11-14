from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.domain.models import CortisolSample
from app.infrastructure.database import get_engine
from app.main import app

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_cortisol():
    with Session(get_engine()) as session:
        session.exec(delete(CortisolSample))
        session.commit()
    yield


def _create_astronaut(
    client: TestClient,
    code: str,
    sex: str = "male",
    birth_date: str = "1985-04-12",
) -> None:
    response = client.post(
        f"{API}/astronauts",
        json={"code": code, "name": "Test", "sex": sex, "birth_date": birth_date},
    )
    assert response.status_code in (201, 409), response.text


def test_create_sample_and_assessment(client: TestClient) -> None:
    _create_astronaut(client, "C-01")

    created = client.post(
        f"{API}/astronauts/C-01/cortisol",
        json={
            "measured_at": "2026-11-13T07:00:00",
            "value": 0.474,
            "unit": "ug_dl",
            "wake_time": "06:00",
            "mission_phase": "inflight",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["band"] == "morning"
    assert body["color"] == 1
    assert body["z"] == pytest.approx(0.0, abs=1e-3)
    assert body["percentile"] == pytest.approx(50.0, abs=0.2)
    assert body["expected_median_ug_dl"] == pytest.approx(0.474, abs=1e-3)
    assert body["mission_phase"] == "inflight"

    assessment = client.get(f"{API}/astronauts/C-01/cortisol?lang=es").json()
    assert assessment["current"]["value_ug_dl"] == pytest.approx(0.474)
    assert len(assessment["samples"]) == 1
    assert assessment["reference"]["age_range"] == [20, 55]
    assert len(assessment["reference"]["curve"]) == 49


def test_nmol_conversion(client: TestClient) -> None:
    _create_astronaut(client, "C-02", sex="female", birth_date="1990-09-23")
    created = client.post(
        f"{API}/astronauts/C-02/cortisol",
        json={
            "measured_at": "2026-11-13T21:00:00",
            "value": 13.077,
            "unit": "nmol_l",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["value_ug_dl"] == pytest.approx(0.474, abs=1e-3)
    assert body["value_nmol_l"] == pytest.approx(13.077, abs=0.05)
    assert body["band"] == "night"
    assert body["color"] == 3


def test_invalid_values_and_future_date(client: TestClient) -> None:
    _create_astronaut(client, "C-03")

    zero = client.post(
        f"{API}/astronauts/C-03/cortisol",
        json={"measured_at": "2026-11-13T07:00:00", "value": 0, "unit": "ug_dl"},
    )
    assert zero.status_code == 422
    assert "cortisol" in zero.json()["detail"].lower()

    future = client.post(
        f"{API}/astronauts/C-03/cortisol",
        json={"measured_at": "2099-01-01T07:00:00", "value": 0.5, "unit": "ug_dl"},
    )
    assert future.status_code == 422
    assert "futuro" in future.json()["detail"].lower()


def test_evening_night_ratio(client: TestClient) -> None:
    _create_astronaut(client, "C-04")
    for moment, value in (
        ("2026-11-13T15:30:00", 0.40),
        ("2026-11-13T21:00:00", 0.10),
    ):
        response = client.post(
            f"{API}/astronauts/C-04/cortisol",
            json={"measured_at": moment, "value": value, "unit": "ug_dl"},
        )
        assert response.status_code == 201, response.text

    assessment = client.get(f"{API}/astronauts/C-04/cortisol").json()
    assert assessment["ratio"]["ratio"] == pytest.approx(4.0)
    assert assessment["ratio"]["reading"] == "watch"
    assert assessment["ratio"]["afternoon_ug_dl"] == pytest.approx(0.40)
    assert assessment["ratio"]["night_ug_dl"] == pytest.approx(0.10)


def test_import_csv(client: TestClient) -> None:
    _create_astronaut(client, "C-05")
    csv_body = (
        "measured_at,value,unit,wake_time,notes\n"
        "2026-11-10 07:00,0.5,ug_dl,06:00,primera\n"
        "2026-11-10 21:00,0.2,ug_dl,,\n"
    )
    response = client.post(
        f"{API}/astronauts/C-05/cortisol/import",
        files={"file": ("cortisol.csv", csv_body.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201, response.text
    report = response.json()
    assert report["created"] == 2
    assert report["errors"] == []

    assessment = client.get(f"{API}/astronauts/C-05/cortisol").json()
    assert len(assessment["samples"]) == 2
    assert assessment["samples"][0]["notes"] == "primera"


def test_age_warning_and_bone_cross(client: TestClient) -> None:
    _create_astronaut(client, "C-06", sex="male", birth_date="1960-01-01")
    for moment, value in (
        ("2026-11-13T07:00:00", 1.20),
        ("2026-11-13T21:00:00", 0.60),
        ("2026-11-12T21:00:00", 0.55),
    ):
        response = client.post(
            f"{API}/astronauts/C-06/cortisol",
            json={"measured_at": moment, "value": value, "unit": "ug_dl"},
        )
        assert response.status_code == 201, response.text

    assessment = client.get(f"{API}/astronauts/C-06/cortisol?lang=es").json()
    assert assessment["bone_cross_risk"] is True
    assert any("cautela" in warning for warning in assessment["warnings"])
    assert any("perdida osea" in warning for warning in assessment["warnings"])


def test_meta_exposes_cortisol_reference(client: TestClient) -> None:
    body = client.get(f"{API}/meta").json()
    assert "cortisol" in body
    assert body["cortisol"]["green_z"] == pytest.approx(1.28)
    assert body["cortisol"]["yellow_z"] == pytest.approx(1.96)
    assert body["cortisol"]["conversion_nmol_per_ug"] == pytest.approx(27.59)
    assert len(body["cortisol"]["curve"]) == 49
