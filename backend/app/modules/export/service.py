"""Exportacion por astronauta: resumen (JSON/HTML/PDF) y datos (JSON/CSV)."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlmodel import Session

from app.core.i18n import t
from app.modules.astronauts import service as astronauts_service
from app.modules.cortisol import service as cortisol_service
from app.modules.mental import service as mental_service
from app.modules.monitoring import service as monitoring_service
from app.modules.radiation import service as radiation_service

COLORS = {
    "green": "#15803d",
    "yellow": "#a16207",
    "orange": "#c2410c",
    "red": "#b91c1c",
    "gray": "#6b7280",
}


def _fmt(value: float | None, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}{suffix}"


def _state(lang: str, color: int | None) -> tuple[str, str]:
    if color == 3:
        return t(lang, "export.status.red"), "red"
    if color == 2:
        return t(lang, "export.status.yellow"), "yellow"
    if color == 1:
        return t(lang, "export.status.green"), "green"
    return t(lang, "export.status.gray"), "gray"


def build_context(session: Session, code: str, lang: str) -> dict[str, Any]:
    astronaut = astronauts_service.get_one(session, code)
    return {
        "astronaut": astronauts_service.to_out(astronaut),
        "bone": monitoring_service.build_assessment(session, code, "calcaneus", lang),
        "cortisol": cortisol_service.build_assessment(session, code, lang),
        "radiation": radiation_service.build_assessment(session, code, lang),
        "mental": mental_service.build_assessment(session, code, lang),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "lang": lang,
    }


def _sections(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    lang = ctx["lang"]
    bone = ctx["bone"]
    cortisol = ctx["cortisol"]
    radiation = ctx["radiation"]
    mental = ctx["mental"]

    sections: list[dict[str, Any]] = []

    if bone.current is not None:
        status, color = _state(lang, bone.current.level)
        sections.append(
            {
                "title": t(lang, "export.bone"),
                "status": status,
                "color": color,
                "rows": [
                    (t(lang, "export.metric.rate"), _fmt(bone.current.rate_pct_month, 2, " %/mes")),
                    (t(lang, "export.metric.bvtv"), _fmt(bone.current.bv_tv, 3)),
                    (
                        t(lang, "export.metric.cumulative"),
                        _fmt(bone.current.cumulative_loss_pct, 1, " %"),
                    ),
                    (t(lang, "export.metric.month"), _fmt(bone.current.month, 1)),
                ],
                "recommendation": " · ".join(bone.recommendations.items),
            }
        )
    else:
        sections.append(
            {
                "title": t(lang, "export.bone"),
                "status": t(lang, "export.no_data"),
                "color": "gray",
                "rows": [],
                "recommendation": "",
            }
        )

    color = cortisol.current.color if cortisol.current else None
    status, tone = _state(lang, color)
    sections.append(
        {
            "title": t(lang, "export.cortisol"),
            "status": status,
            "color": tone,
            "rows": (
                [
                    (
                        t(lang, "export.metric.band"),
                        t(lang, f"cortisol.band.{cortisol.current.band}"),
                    ),
                    ("Z", _fmt(cortisol.current.z, 2)),
                    ("µg/dL", _fmt(cortisol.current.value_ug_dl, 2)),
                    ("nmol/L", _fmt(cortisol.current.value_nmol_l, 1)),
                ]
                if cortisol.current
                else []
            ),
            "recommendation": t(lang, f"rec.cortisol.{color or 0}"),
        }
    )

    color = radiation.color
    status, tone = _state(lang, color)
    sections.append(
        {
            "title": t(lang, "export.radiation"),
            "status": status,
            "color": tone,
            "rows": (
                [
                    ("µSv/min", _fmt(radiation.current.eq_rate_usv_min, 2)),
                    ("F30", _fmt(radiation.cumulative.f30, 2)),
                    ("F carrera", _fmt(radiation.cumulative.f_career, 2)),
                    (
                        t(lang, "export.metric.layer_a"),
                        t(lang, f"radiation.layer.status.{radiation.layers['a'].status}"),
                    ),
                ]
                if radiation.current
                else []
            ),
            "recommendation": t(lang, f"rec.radiation.{color or 0}"),
        }
    )

    current = mental.current
    status = t(lang, f"export.zone.{current.zone}") if current else t(lang, "export.no_data")
    tone = current.zone if current else "gray"
    sections.append(
        {
            "title": t(lang, "export.mental"),
            "status": status,
            "color": tone,
            "rows": (
                [
                    ("ALI", _fmt(current.ali, 1)),
                    ("DMRS", _fmt(current.dmrs, 1)),
                    (t(lang, "export.metric.wl"), _fmt(current.wl_day, 1)),
                    (t(lang, "export.metric.ewma"), _fmt(current.ewma_mood, 1)),
                ]
                if current
                else []
            ),
            "recommendation": t(lang, f"rec.mental.{current.zone}") if current else "",
        }
    )

    return sections


def summary_payload(ctx: dict[str, Any]) -> dict[str, Any]:
    sections = _sections(ctx)
    return {
        "generated_at": ctx["generated_at"],
        "astronaut": ctx["astronaut"].model_dump(mode="json"),
        "sections": sections,
        "disclaimer": t(ctx["lang"], "export.disclaimer"),
    }


def summary_json(session: Session, code: str, lang: str) -> dict[str, Any]:
    return summary_payload(build_context(session, code, lang))


def summary_html(session: Session, code: str, lang: str) -> str:
    ctx = build_context(session, code, lang)
    payload = summary_payload(ctx)
    astronaut = ctx["astronaut"]

    cards = []
    for section in payload["sections"]:
        color = COLORS.get(section["color"], COLORS["gray"])
        rows = "".join(
            f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>"
            for label, value in section["rows"]
        )
        recommendation = (
            f"<p class='rec'><strong>{escape(t(lang, 'export.recommendation'))}:</strong> "
            f"{escape(section['recommendation'])}</p>"
            if section["recommendation"]
            else ""
        )
        cards.append(
            f"""
            <section class="card" style="border-left-color:{color}">
              <header>
                <h2>{escape(section["title"])}</h2>
                <span class="pill" style="color:{color};border-color:{color}">
                  {escape(section["status"])}
                </span>
              </header>
              <table>{rows}</table>
              {recommendation}
            </section>
            """
        )

    profile = [astronaut.code, astronaut.name]
    if astronaut.age is not None:
        profile.append(f"{astronaut.age} años")
    if astronaut.sex:
        profile.append(t(lang, f"sex.{astronaut.sex}"))

    return f"""<!doctype html>
<html lang="{escape(lang)}">
<head>
<meta charset="utf-8" />
<title>{escape(t(lang, "export.title"))} · {escape(astronaut.code)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #f6f7f9; color: #14181f;
         font: 14px/1.5 Arial, Helvetica, sans-serif; }}
  .page {{ max-width: 820px; margin: 24px auto; padding: 28px; background: #fff;
           border: 1px solid #dfe3e9; border-radius: 12px; }}
  .brand {{ font-size: 11px; letter-spacing: .24em; text-transform: uppercase; color: #5b6574; }}
  h1 {{ font-size: 26px; margin: 6px 0 4px; letter-spacing: .04em; text-transform: uppercase; }}
  .profile {{ margin: 0 0 2px; font-weight: 600; }}
  .meta {{ margin: 0 0 22px; color: #5b6574; font-size: 12px; }}
  .card {{ border: 1px solid #dfe3e9; border-left: 5px solid #6b7280; border-radius: 10px;
           padding: 14px 16px; margin-bottom: 14px; }}
  .card header {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
  .card h2 {{ font-size: 13px; margin: 0; text-transform: uppercase; letter-spacing: .08em; }}
  .pill {{ font-size: 11px; font-weight: 700; border: 1px solid;
           border-radius: 999px; padding: 2px 10px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th, td {{ text-align: left; padding: 4px 0; font-size: 13px; }}
  th {{ color: #5b6574; font-weight: 500; }}
  td {{ text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }}
  .rec {{ margin: 10px 0 0; font-size: 12px; color: #374151; }}
  footer {{ margin-top: 18px; color: #5b6574; font-size: 11px; }}
  @media print {{
    body {{ background: #fff; }}
    .page {{ border: 0; margin: 0; padding: 0; max-width: none; }}
  }}
</style>
</head>
<body>
  <main class="page">
    <p class="brand">Astro Health Monitor · NASA SPACE</p>
    <h1>{escape(t(lang, "export.title"))}</h1>
    <p class="profile">{escape(" · ".join(str(part) for part in profile))}</p>
    <p class="meta">{escape(t(lang, "export.generated"))}: {escape(payload["generated_at"])}</p>
    {"".join(cards)}
    <footer>{escape(payload["disclaimer"])}</footer>
  </main>
</body>
</html>"""


def summary_pdf(session: Session, code: str, lang: str) -> bytes:
    ctx = build_context(session, code, lang)
    payload = summary_payload(ctx)
    astronaut = ctx["astronaut"]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{t(lang, 'export.title')} {astronaut.code}",
    )
    styles = getSampleStyleSheet()
    brand = ParagraphStyle(
        "brand",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#5b6574"),
        spaceAfter=3,
    )
    title = ParagraphStyle(
        "title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, spaceAfter=4
    )
    profile = ParagraphStyle("profile", parent=styles["Normal"], fontSize=10, spaceAfter=2)
    meta = ParagraphStyle(
        "meta",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#5b6574"),
        spaceAfter=10,
    )
    module = ParagraphStyle(
        "module",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceBefore=8,
        spaceAfter=4,
    )
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.5, leading=11)
    rec = ParagraphStyle("rec", parent=body, textColor=colors.HexColor("#374151"), spaceBefore=3)

    profile_text = " · ".join(
        str(part)
        for part in [
            astronaut.code,
            astronaut.name,
            f"{astronaut.age} años" if astronaut.age else None,
            t(lang, f"sex.{astronaut.sex}") if astronaut.sex else None,
        ]
        if part
    )

    elements: list[Any] = [
        Paragraph("ASTRO HEALTH MONITOR · NASA SPACE", brand),
        Paragraph(escape(t(lang, "export.title")), title),
        Paragraph(escape(profile_text), profile),
        Paragraph(
            f"{escape(t(lang, 'export.generated'))}: {escape(payload['generated_at'])}", meta
        ),
    ]

    for section in payload["sections"]:
        tone = COLORS.get(section["color"], COLORS["gray"])
        elements.append(Paragraph(escape(section["title"]), module))
        rows = [
            [Paragraph(f"<b>{escape(str(label))}</b>", body), Paragraph(escape(str(value)), body)]
            for label, value in section["rows"]
        ]
        if rows:
            table = Table(rows, colWidths=[110 * mm, 55 * mm])
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#14181f")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            elements.append(table)
        elements.append(
            Paragraph(
                f"<font color='{tone}'><b>{escape(section['status'])}</b></font>",
                body,
            )
        )
        if section["recommendation"]:
            label = escape(t(lang, "export.recommendation"))
            text = f"<b>{label}:</b> {escape(section['recommendation'])}"
            elements.append(Paragraph(text, rec))
        elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph(escape(payload["disclaimer"]), meta))
    doc.build(elements)
    return buffer.getvalue()


def data_json(session: Session, code: str, lang: str) -> dict[str, Any]:
    ctx = build_context(session, code, lang)
    return {
        "generated_at": ctx["generated_at"],
        "astronaut": ctx["astronaut"].model_dump(mode="json"),
        "bone": ctx["bone"].model_dump(mode="json"),
        "cortisol": ctx["cortisol"].model_dump(mode="json"),
        "radiation": ctx["radiation"].model_dump(mode="json"),
        "mental": ctx["mental"].model_dump(mode="json"),
    }


CSV_HEADER = ["module", "recorded_at", "metric", "value", "unit", "flags", "notes"]


def data_csv(session: Session, code: str, lang: str) -> str:
    ctx = build_context(session, code, lang)
    rows: list[list[Any]] = []

    for point in ctx["bone"].points:
        stamp = point.measured_on.isoformat()
        rows.append(["bone", stamp, "bua", point.bua, "dB/MHz", "", ""])
        rows.append(["bone", stamp, "uv", point.uv, "m/s", "", ""])
        if point.att is not None:
            rows.append(["bone", stamp, "att", point.att, "dB/cm", "", ""])
        rows.append(["bone", stamp, "bv_tv", point.bv_tv, "ratio", "", ""])
        rows.append(["bone", stamp, "cumulative_loss_pct", point.cumulative_loss_pct, "%", "", ""])
        rows.append(["bone", stamp, "rate_pct_month", point.rate_pct_month, "%/month", "", ""])
        rows.append(["bone", stamp, "level", point.level, "index", point.bone_status, ""])

    for sample in ctx["cortisol"].samples:
        stamp = sample.measured_at.isoformat()
        flags = "|".join(sample.flags)
        rows.append(
            ["cortisol", stamp, "value", sample.value_ug_dl, "ug/dL", flags, sample.notes or ""]
        )
        rows.append(["cortisol", stamp, "value", sample.value_nmol_l, "nmol/L", flags, ""])
        rows.append(["cortisol", stamp, "z", sample.z, "sd", flags, ""])
        rows.append(["cortisol", stamp, "percentile", sample.percentile, "%", flags, ""])
        rows.append(["cortisol", stamp, "color", sample.color, "index", flags, ""])

    for reading in ctx["radiation"].readings:
        stamp = reading.measured_at.isoformat()
        rows.append(
            [
                "radiation",
                stamp,
                "eq_rate",
                reading.eq_rate_usv_min,
                "uSv/min",
                reading.region,
                reading.notes or "",
            ]
        )
        if reading.dose_rate_ugy_min is not None:
            rows.append(
                [
                    "radiation",
                    stamp,
                    "dose_rate",
                    reading.dose_rate_ugy_min,
                    "uGy/min",
                    reading.region,
                    "",
                ]
            )
        if reading.q_factor is not None:
            rows.append(
                ["radiation", stamp, "q_factor", reading.q_factor, "ratio", reading.region, ""]
            )

    for day in ctx["mental"].days:
        stamp = day.day.isoformat()
        rows.append(["mental", stamp, "wl_day", day.wl_day, "index", day.zone, ""])
        rows.append(["mental", stamp, "dmrs", day.dmrs, "index", day.zone, ""])
        rows.append(["mental", stamp, "ali", day.ali, "index", day.zone, ""])
        rows.append(["mental", stamp, "pa", day.pa, "index", day.zone, ""])
        rows.append(["mental", stamp, "na", day.na, "index", day.zone, ""])
        for task in day.tasks:
            rows.append(
                [
                    "mental_task",
                    stamp,
                    "overall",
                    task.overall,
                    "index",
                    task.eval_mode,
                    task.name or task.task_ref or "",
                ]
            )
            rows.append(
                ["mental_task", stamp, "duration_min", task.duration_min, "min", task.eval_mode, ""]
            )

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    writer.writerows(rows)
    return "\ufeff" + buffer.getvalue()
