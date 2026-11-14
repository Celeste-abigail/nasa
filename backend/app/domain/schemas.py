"""Contratos HTTP (Pydantic). La validacion cientifica vive en domain/."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Site = Literal["calcaneus", "femoral_neck"]
Sex = Literal["male", "female"]
BoneStatus = Literal["normal", "osteopenia", "osteoporosis", "unknown"]


class AstronautCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32, examples=["AST-03"])
    name: str = Field(default="", max_length=120)
    sex: Sex
    birth_date: date


class AstronautUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    birth_date: date | None = None


class AstronautOut(BaseModel):
    code: str
    name: str
    sex: Sex | None = None
    birth_date: date | None = None
    age: int | None = None


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


class ReferenceMetricOut(BaseModel):
    mean: float
    sd: float
    z: float | None
    t: float | None
    status: BoneStatus


class ReferenceOut(BaseModel):
    sex: Sex
    age: int
    age_band: str
    n: int
    clamped: bool
    source: str
    population: str
    bua: ReferenceMetricOut
    sos: ReferenceMetricOut
    status: BoneStatus


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
    # Referencia poblacional (None si falta sexo o fecha de nacimiento)
    bua_z: float | None = None
    sos_z: float | None = None
    bua_t: float | None = None
    sos_t: float | None = None
    bone_status: BoneStatus = "unknown"


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
    reference: ReferenceOut | None
    warnings: list[str]
    model: ModelInfo


class ImportRowError(BaseModel):
    line: int
    message: str


class ImportReport(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError]


class ReferenceInfoOut(BaseModel):
    source: str
    population: str
    bua_unit: str
    sos_unit: str
    age_bands: list[str]
    t_thresholds: dict[str, float]


class MetaOut(BaseModel):
    app_name: str
    model: ModelInfo
    sites: list[str]
    languages: list[str]
    thresholds: dict[str, float]
    units: dict[str, str]
    reference: ReferenceInfoOut


class ErrorBody(BaseModel):
    detail: str
    code: str | None = None
    fields: dict[str, str] | None = None
