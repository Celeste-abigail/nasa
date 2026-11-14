from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.domain.models import RadiationReading
from app.infrastructure.database import get_engine
from app.main import app

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_radiation():
    with Session(get_engine()) as session:
        session.exec(delete(RadiationReading))
        session.commit()
    yield


def _create_astronaut(client: TestClient, code: str) -> None:
    response = client.post(
        f"{API}/astronauts",
        json={
            "code": code,
            "name": "Radiation test",
            "sex": "male",
            "birth_date": "1985-04-12",
        },
    )
    assert response.status_code in (201, 409), response.text


def _post(client: TestClient, code: str, moment: str, eq: float, **extra):
    return client.post(
        f"{API}/astronauts/{code}/radiation",
        json={"measured_at": moment, "eq_rate": eq, "region": "unknown", **extra},
    )


def test_reading_flow(client: TestClient) -> None:
    _create_astronaut(client, "R-01")
    created = _post(client, "R-01", "2018-04-11T10:00:00", 0.5)
    assert created.status_code == 201, created.text

    assessment = client.get(f"{API}/astronauts/R-01/radiation?lang=es").json()
    assert assessment["current"]["eq_rate_usv_min"] == pytest.approx(0.5)
    assert assessment["layers"]["a"]["color"] == 1
    assert assessment["layers"]["b"]["status"] == "insufficient"
    assert assessment["layers"]["c"]["status"] == "insufficient"
    assert assessment["color"] == 1
    assert assessment["reference"]["used_fallback"] is True
    assert assessment["reference"]["daily_available"] is False
    assert any("referencia" in warning.lower() for warning in assessment["warnings"])


def test_high_single_reading_is_yellow_and_sustained_is_red(client: TestClient) -> None:
    _create_astronaut(client, "R-02")
    _post(client, "R-02", "2018-04-11T12:00:00", 20.0)
    first = client.get(f"{API}/astronauts/R-02/radiation").json()
    assert first["layers"]["a"]["color"] == 2
    assert first["layers"]["a"]["detail"] == "above_p99_single"

    _post(client, "R-02", "2018-04-11T12:01:00", 21.0)
    _post(client, "R-02", "2018-04-11T12:02:00", 22.0)
    third = client.get(f"{API}/astronauts/R-02/radiation").json()
    assert third["layers"]["a"]["color"] == 3
    assert third["layers"]["a"]["detail"] == "above_p99_sustained"


def test_career_fraction_with_prior_dose(client: TestClient) -> None:
    _create_astronaut(client, "R-03")
    _post(client, "R-03", "2018-04-11T08:00:00", 0.4, prior_career_msv=560.0)
    assessment = client.get(f"{API}/astronauts/R-03/radiation").json()
    assert assessment["cumulative"]["f_career"] == pytest.approx(560.0 / 600.0, abs=1e-3)
    assert assessment["layers"]["c"]["color"] == 3
    assert assessment["color"] == 3


def test_invalid_and_future_readings(client: TestClient) -> None:
    _create_astronaut(client, "R-04")

    zero = _post(client, "R-04", "2018-04-11T10:00:00", 0.0)
    assert zero.status_code == 422
    assert "uSv/min" in zero.json()["detail"]

    future = _post(client, "R-04", "2099-01-01T10:00:00", 0.5)
    assert future.status_code == 422
    assert "futuro" in future.json()["detail"].lower()


def test_meta_exposes_radiation_reference(client: TestClient) -> None:
    body = client.get(f"{API}/meta").json()
    assert "radiation" in body
    assert body["radiation"]["limits"]["career_msv"] == 600.0
    assert body["radiation"]["thresholds"]["persistence"] == 3.0
    assert body["radiation"]["period"]["days"] == 1
