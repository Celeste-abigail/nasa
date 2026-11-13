"""Contratos HTTP (Pydantic). La validacion cientifica vive en domain/bone.py."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Site = Literal["calcaneus", "femoral_neck"]


class AstronautCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32, examples=["AST-03"])
    name: str = Field(default="", max_length=120)


class AstronautOut(BaseModel):
    code: str
    name: str


class MeasurementCreate(BaseModel):
    measured_on: date
    site: Site = "calcaneus"
    bua: float
    uv: float
    att: float | None = None


class MeasurementOut(BaseModel):
    id: int
    measured_on: date
    site: Site
    bua: float
    uv: float
    att: float | None
    source: str


class PointOut(BaseModel):
    measured_on: date
    day: int
    bua: float
    uv: float
    att: float | None
    bv_tv: float
    cumulative_loss_pct: float
    rate_pct_month: float | None
    bv_tv_cumulative_loss_pct: float
    level: int
    level_name: str
    level_tip: str


class ModelInfo(BaseModel):
    version: str
    formula: str
    references: list[str]


class AssessmentOut(BaseModel):
    astronaut: AstronautOut
    site: Site
    baseline: PointOut | None
    points: list[PointOut]
    current: PointOut | None
    warnings: list[str]
    model: ModelInfo


class ImportRowError(BaseModel):
    line: int
    message: str


class ImportReport(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError]


class MetaOut(BaseModel):
    app_name: str
    model: ModelInfo
    sites: list[str]
    languages: list[str]
    thresholds: dict[str, float]
    units: dict[str, str]


class ErrorBody(BaseModel):
    detail: str
    code: str | None = None
    fields: dict[str, str] | None = None
