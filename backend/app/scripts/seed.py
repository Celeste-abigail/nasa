"""Datos de ejemplo (perfil, series y cuestionarios) para demos.

Uso:  uv run python -m app.scripts.seed [--force]
"""

from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta

from sqlmodel import Session

from app.domain import mental
from app.domain.schemas import (
    CdaInput,
    CortisolSampleCreate,
    PvtInput,
    RadiationReadingCreate,
    SleepNightIn,
    SleepProfileIn,
    TlxComparisonIn,
    TlxSessionCreate,
)
from app.infrastructure import repositories
from app.infrastructure.database import get_engine, init_db
from app.modules.astronauts import service as astronauts_service
from app.modules.cortisol import service as cortisol_service
from app.modules.measurements import service as measurements_service
from app.modules.mental import service as mental_service
from app.modules.radiation import service as radiation_service

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

# (momento ISO, valor, unidad, hora de despertar)
CORTISOL = {
    "AST-01": [
        ("2026-07-01T07:00:00", 0.52, "ug_dl", "06:00"),
        ("2026-07-01T12:00:00", 0.34, "ug_dl", "06:00"),
        ("2026-07-01T15:30:00", 0.24, "ug_dl", "06:00"),
        ("2026-07-01T21:00:00", 0.15, "ug_dl", "06:00"),
        ("2026-07-02T07:00:00", 0.58, "ug_dl", "06:10"),
        ("2026-07-02T21:00:00", 0.36, "ug_dl", "06:10"),
    ],
    "AST-02": [
        ("2026-07-01T07:00:00", 0.55, "ug_dl", "05:50"),
        ("2026-07-01T15:30:00", 0.28, "ug_dl", "05:50"),
        ("2026-07-01T21:00:00", 0.18, "ug_dl", "05:50"),
    ],
}

# (momento UTC, tasa eq uSv/min, region, dia de mision, dosis previa)
RADIATION = {
    "AST-01": [
        ("2018-04-11T08:00:00", 0.45, "unknown", 20, None),
        ("2018-04-11T10:00:00", 0.60, "unknown", 20, None),
        ("2018-04-11T12:00:00", 1.10, "unknown", 20, None),
        ("2018-04-11T12:05:00", 2.20, "unknown", 20, None),
    ]
}

TLX_CHOICES = [
    "MD",
    "MD",
    "OP",
    "EF",
    "MD",
    "PD",
    "OP",
    "PD",
    "PD",
    "OP",
    "EF",
    "FR",
    "OP",
    "FR",
    "EF",
]
TLX_VALUES = {
    "AST-01": [55.0, 60.0, 60.0, 65.0, 60.0, 70.0],
    "AST-02": [50.0, 55.0, 60.0],
}
CDA_DAYS = {"AST-01": 14, "AST-02": 7}
SLEEP_TST = {"AST-01": [375, 400, 420, 350, 390, 410, 380], "AST-02": [380, 395, 405, 390, 400]}
PVT_TRIALS = {
    "AST-01": [
        [240, 245, 250, 235, 255, 244, 248, 251, 238, 247],
        [242, 246, 249, 236, 252, 241, 247, 250, 239, 245],
        [238, 244, 251, 237, 253, 242, 246, 249, 240, 243],
        [241, 247, 250, 236, 254, 243, 248, 252, 239, 246],
        [243, 245, 248, 238, 251, 244, 247, 250, 240, 249],
        [245, 260, 231, 298, 410, 252, 240, 367, 229, 275, 90, 255],
    ],
    "AST-02": [
        [250, 255, 260, 248, 262, 252, 258, 261, 249, 256],
        [252, 257, 259, 249, 263, 253, 258, 260, 250, 255],
        [248, 254, 261, 247, 264, 251, 257, 259, 249, 253],
    ],
}


def _comparisons() -> list[TlxComparisonIn]:
    return [
        TlxComparisonIn(pair=list(pair), choice=choice)
        for pair, choice in zip(mental.PAIRS, TLX_CHOICES, strict=True)
    ]


def _cda_items(index: int) -> dict[str, int]:
    sway = index % 4
    raw = {
        "animo": 8 - sway // 2,
        "energia": 7 - sway // 2,
        "motivacion": 8 - sway // 3,
        "tension": 2 + sway,
        "tristeza": 2 + sway // 2,
        "irritabilidad": 3 + sway // 2,
        "estres": 4 + sway,
        "fatiga_mental": 5 + sway,
        "sueno": 7 - sway // 2,
        "conexion": 8 - sway // 3,
    }
    return {key: max(0, min(10, value)) for key, value in raw.items()}


def _seed_mental(session: Session, code: str) -> None:
    tlx_base = datetime(2026, 11, 1, 18, 0)
    for index, value in enumerate(TLX_VALUES.get(code, [])):
        mental_service.record_tlx(
            session,
            code,
            TlxSessionCreate(
                taken_at=tlx_base + timedelta(days=index),
                task_description=f"Tarea de ejemplo {index + 1}",
                task_category="EVA" if index % 2 == 0 else "Robotica",
                duration_min=90,
                ratings={dimension: int(value) for dimension in mental.DIMENSIONS},
                comparisons=_comparisons(),
            ),
            "es",
        )

    for index in range(CDA_DAYS.get(code, 0)):
        mental_service.upsert_cda(
            session,
            code,
            date(2026, 10, 20) + timedelta(days=index),
            CdaInput(items=_cda_items(index)),
            "es",
        )

    mental_service.save_profile(
        session,
        code,
        SleepProfileIn(
            need_hours=7.5,
            scheduled_wake="06:00",
            window_minutes=450,
            blocked=False,
        ),
        "es",
    )
    for index, tst in enumerate(SLEEP_TST.get(code, [])):
        day = date(2026, 11, 2) + timedelta(days=index)
        entry = datetime.combine(day - timedelta(days=1), time(22, 30))
        final = entry + timedelta(minutes=25 + 40 + tst)
        exit_at = final + timedelta(minutes=20)
        mental_service.upsert_sleep(
            session,
            code,
            SleepNightIn(
                day=day,
                entry_at=entry,
                latency_min=25,
                awakenings=2,
                waso_min=40,
                cause_group="A" if index % 3 else "B",
                cause_detail="work" if index % 3 else "noise",
                final_wake_at=final,
                exit_at=exit_at,
                quality=6,
                inertia=8 if index == 2 else 3,
                dreams="nightmare" if index == 4 else "neutral",
                environmental=["nothing"],
                nap_min=0,
            ),
            "es",
        )

    pvt_base = datetime(2026, 11, 1, 10, 0)
    for index, trials in enumerate(PVT_TRIALS.get(code, [])):
        mental_service.record_pvt(
            session,
            code,
            PvtInput(
                taken_at=pvt_base + timedelta(days=index),
                mode=60,
                trials=trials,
                false_starts=0,
                subjective_alertness=8 if index == len(PVT_TRIALS[code]) - 1 else 5,
            ),
            "es",
        )


def main() -> int:
    init_db()
    base = date(2026, 7, 1)
    force = "--force" in sys.argv

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
            if existing and not force:
                print(f"{code}: ya tiene {len(existing)} mediciones, se omite")
            else:
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

            existing_cortisol = repositories.list_cortisol_samples(session, astronaut.id or 0)
            if existing_cortisol and not force:
                print(f"{code}: ya tiene {len(existing_cortisol)} muestras de cortisol")
            else:
                rows = CORTISOL.get(code, [])
                for moment, value, unit, wake in rows:
                    cortisol_service.record(
                        session=session,
                        code=astronaut.code,
                        payload=CortisolSampleCreate(
                            measured_at=datetime.fromisoformat(moment),
                            value=value,
                            unit=unit,
                            wake_time=time.fromisoformat(wake),
                            mission_phase="analog",
                        ),
                        lang="es",
                        source="seed",
                    )
                print(f"{code}: {len(rows)} muestras de cortisol cargadas")

            existing_radiation = repositories.list_radiation_readings(session, astronaut.id or 0)
            if existing_radiation and not force:
                print(f"{code}: ya tiene {len(existing_radiation)} lecturas de radiacion")
            else:
                rows = RADIATION.get(code, [])
                for moment, eq, region, mission_day, prior in rows:
                    radiation_service.record(
                        session=session,
                        code=astronaut.code,
                        payload=RadiationReadingCreate(
                            measured_at=datetime.fromisoformat(moment),
                            eq_rate=eq,
                            region=region,  # type: ignore[arg-type]
                            mission_day=mission_day,
                            prior_career_msv=prior,
                        ),
                        lang="es",
                        source="seed",
                    )
                print(f"{code}: {len(rows)} lecturas de radiacion cargadas")

            existing_mental = repositories.list_tlx_sessions(session, astronaut.id or 0)
            if existing_mental and not force:
                print(f"{code}: ya tiene {len(existing_mental)} sesiones TLX")
            else:
                _seed_mental(session, astronaut.code)
                print(
                    f"{code}: {len(TLX_VALUES.get(code, []))} TLX, "
                    f"{CDA_DAYS.get(code, 0)} CDA, "
                    f"{len(SLEEP_TST.get(code, []))} noches, "
                    f"{len(PVT_TRIALS.get(code, []))} PVT"
                )

    print("listo: backend/data/nasa_space.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
