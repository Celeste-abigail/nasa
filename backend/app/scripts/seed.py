"""Datos de ejemplo (perfil + serie) para demos.

Uso:  uv run python -m app.scripts.seed [--force]
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from sqlmodel import Session

from app.infrastructure.database import get_engine, init_db
from app.modules.astronauts import service as astronauts_service
from app.modules.measurements import service as measurements_service

# (offset en dias desde la linea base, BUA dB/MHz, UV m/s, ATT dB/cm)
DEMO = {
    "AST-01": {
        "name": "Astronaut One",
        "sex": "male",
        "birth_date": date(1985, 4, 12),
        "rows": [
            (0, 118.0, 1552.0, 52.0),
            (15, 117.9, 1551.0, 52.0),
            (30, 117.3, 1548.0, 51.6),
            (60, 115.9, 1542.0, 50.9),
            (90, 114.2, 1536.0, 50.1),
        ],
    },
    "AST-02": {
        "name": "Astronaut Two",
        "sex": "female",
        "birth_date": date(1990, 9, 23),
        "rows": [
            (0, 113.8, 1550.0, 50.0),
            (30, 113.5, 1549.0, 49.8),
        ],
    },
}


def main() -> int:
    init_db()
    base = date(2026, 7, 1)
    with Session(get_engine()) as session:
        for code, profile in DEMO.items():
            astronaut = astronauts_service.ensure(
                session,
                code,
                profile["name"],
                sex=profile["sex"],
                birth_date=profile["birth_date"],
            )
            existing = measurements_service.list_for(session, astronaut.code, site="calcaneus")
            if existing and "--force" not in sys.argv:
                print(f"{code}: ya tiene {len(existing)} mediciones, se omite")
                continue
            for offset, bua, uv, att in profile["rows"]:
                measurements_service.record(
                    session=session,
                    code=astronaut.code,
                    measured_on=base + timedelta(days=offset),
                    site="calcaneus",
                    bua=bua,
                    uv=uv,
                    att=att,
                    lang="es",
                    source="seed",
                )
            print(f"{code}: {len(profile['rows'])} mediciones cargadas")
    print("listo: backend/data/nasa_space.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
