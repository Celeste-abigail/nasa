"""Datos de ejemplo (los mismos del prototipo HTML) para demos.

Uso:  uv run python -m app.scripts.seed [--force]
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from sqlmodel import Session

from app.infrastructure.database import get_engine, init_db
from app.modules.astronauts import service as astronauts_service
from app.modules.measurements import service as measurements_service

DEMO = {
    "AST-01": [
        # (offset en días desde la línea base, BUA, UV, ATT)
        (0, 78.0, 1560.0, 52.0),
        (15, 77.9, 1559.0, 52.0),
        (30, 77.5, 1556.0, 51.6),
        (60, 76.6, 1550.0, 50.9),
        (90, 75.5, 1543.0, 50.1),
    ],
    "AST-02": [
        (0, 76.0, 1552.0, 50.0),
        (30, 75.8, 1551.0, 49.8),
    ],
}


def main() -> int:
    init_db()
    base = date(2026, 7, 1)
    with Session(get_engine()) as session:
        for code, rows in DEMO.items():
            astronaut = astronauts_service.ensure(session, code, f"Astronaut {code[-2:]}")
            existing = measurements_service.list_for(session, astronaut.code, site="calcaneus")
            if existing and "--force" not in sys.argv:
                print(f"{code}: ya tiene {len(existing)} mediciones, se omite")
                continue
            for offset, bua, uv, att in rows:
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
            print(f"{code}: {len(rows)} mediciones cargadas")
    print("listo: backend/data/nasa_space.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
