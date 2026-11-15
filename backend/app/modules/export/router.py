from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_lang
from app.infrastructure.database import get_session
from app.modules.export import service

router = APIRouter(prefix="/astronauts/{code}/export", tags=["export"])


def _filename(code: str, extension: str) -> str:
    return f"nasa-space-{code}-{date.today().isoformat()}.{extension}"


def _attachment(content: bytes | str, media_type: str, filename: str) -> Response:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary.json")
def export_summary_json(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> Response:
    payload = service.summary_json(session, code, lang)
    return _attachment(
        json.dumps(payload, ensure_ascii=False, indent=2),
        "application/json",
        _filename(code, "summary.json"),
    )


@router.get("/summary.html")
def export_summary_html(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> Response:
    document = service.summary_html(session, code, lang)
    return Response(
        content=document.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'inline; filename="{_filename(code, "summary.html")}"'},
    )


@router.get("/summary.pdf")
def export_summary_pdf(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> Response:
    document = service.summary_pdf(session, code, lang)
    return _attachment(document, "application/pdf", _filename(code, "summary.pdf"))


@router.get("/data.json")
def export_data_json(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> Response:
    payload = service.data_json(session, code, lang)
    return _attachment(
        json.dumps(payload, ensure_ascii=False, indent=2),
        "application/json",
        _filename(code, "data.json"),
    )


@router.get("/data.csv")
def export_data_csv(
    code: str,
    session: Session = Depends(get_session),
    lang: str = Depends(get_lang),
) -> Response:
    document = service.data_csv(session, code, lang)
    return _attachment(document, "text/csv; charset=utf-8", _filename(code, "data.csv"))
