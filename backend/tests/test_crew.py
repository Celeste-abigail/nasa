from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain.errors import ConflictError
from app.infrastructure import repositories
from app.infrastructure.database import get_engine
from app.main import app
from app.modules.astronauts import service

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _create(client: TestClient, code: str) -> None:
    response = client.post(
        f"{API}/astronauts",
        json={
            "code": code,
            "name": "Crew test",
            "sex": "female",
            "birth_date": "1990-05-05",
        },
    )
    assert response.status_code in (201, 409), response.text


def test_archive_restore_keeps_data(client: TestClient) -> None:
    _create(client, "CREW-1")
    created = client.post(
        f"{API}/astronauts/CREW-1/measurements",
        json={
            "measured_on": "2026-10-01",
            "site": "calcaneus",
            "bua": 115.0,
            "uv": 1545.0,
            "att": None,
        },
    )
    assert created.status_code == 201, created.text

    archived = client.delete(f"{API}/astronauts/CREW-1")
    assert archived.status_code == 200, archived.text

    active_codes = [item["code"] for item in client.get(f"{API}/astronauts").json()]
    assert "CREW-1" not in active_codes
    archived_codes = [item["code"] for item in client.get(f"{API}/astronauts/archived").json()]
    assert "CREW-1" in archived_codes

    blocked = client.get(f"{API}/astronauts/CREW-1/monitoring")
    assert blocked.status_code == 404

    restored = client.post(f"{API}/astronauts/CREW-1/restore")
    assert restored.status_code == 200, restored.text

    monitoring = client.get(f"{API}/astronauts/CREW-1/monitoring").json()
    assert len(monitoring["points"]) == 1
    assert monitoring["points"][0]["bua"] == pytest.approx(115.0)

    # Limpieza: archivar de nuevo para no dejar rastro en otros tests de lista.
    client.delete(f"{API}/astronauts/CREW-1")


def test_cannot_archive_the_last_active_astronaut(monkeypatch) -> None:
    with Session(get_engine()) as session:
        astronaut = repositories.get_astronaut(session, "ONLY-1")
        if astronaut is None:
            astronaut = repositories.create_astronaut(
                session, "ONLY-1", "Solo", "male", date(1985, 1, 1)
            )

        monkeypatch.setattr(
            repositories,
            "list_astronauts",
            lambda _session, include_archived=False: [astronaut],
        )
        with pytest.raises(ConflictError) as error:
            service.archive(session, "ONLY-1")
        assert error.value.key == "error.last_astronaut"
