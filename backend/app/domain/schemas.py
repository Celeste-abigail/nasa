"""Contratos HTTP (Pydantic). La validacion cientifica vive en domain/."""

from __future__ import annotations

from datetime import date, datetime, time
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


# --- Modulo cortisol (independiente del oseo) ---

CortisolUnit = Literal["ug_dl", "nmol_l"]
MissionPhase = Literal["preflight", "inflight", "postflight", "analog"]
Reading = Literal["normal", "watch", "elevated", "flat"]


class CortisolSampleCreate(BaseModel):
    measured_at: datetime
    value: float
    unit: CortisolUnit = "ug_dl"
    wake_time: time | None = None
    mission_phase: MissionPhase | None = None
    notes: str | None = Field(default=None, max_length=500)


class CortisolSampleOut(BaseModel):
    id: int
    measured_at: datetime
    value_ug_dl: float
    value_nmol_l: float
    hour: float
    band: str
    z: float
    percentile: float
    color: int
    expected_median_ug_dl: float
    expected_median_nmol_l: float
    direction: Literal["high", "low"]
    sex_color: int
    discordant: bool
    above_manufacturer_p95: bool
    flags: list[str]
    wake_time: time | None
    mission_phase: MissionPhase | None
    notes: str | None


class CortisolRatioOut(BaseModel):
    date: date
    ratio: float
    reading: Reading
    afternoon_ug_dl: float
    night_ug_dl: float


class CortisolBaselineOut(BaseModel):
    band: str
    n: int
    median_ug_dl: float
    delta_pct: float | None


class CortisolCurvePointOut(BaseModel):
    hour: float
    median_ug_dl: float
    p10_ug_dl: float
    p90_ug_dl: float


class CortisolReferenceOut(BaseModel):
    method: str
    source: str
    sigma_ln: float
    green_z: float
    yellow_z: float
    conversion_nmol_per_ug: float
    age_range: list[int]
    curve: list[CortisolCurvePointOut]


class CortisolAssessmentOut(BaseModel):
    astronaut: AstronautOut
    samples: list[CortisolSampleOut]
    current: CortisolSampleOut | None
    ratio: CortisolRatioOut | None
    personal_baseline: CortisolBaselineOut | None
    bone_cross_risk: bool
    warnings: list[str]
    reference: CortisolReferenceOut


class MetaOut(BaseModel):
    app_name: str
    model: ModelInfo
    sites: list[str]
    languages: list[str]
    thresholds: dict[str, float]
    units: dict[str, str]
    reference: ReferenceInfoOut
    cortisol: CortisolReferenceOut


class ErrorBody(BaseModel):
    detail: str
    code: str | None = None
    fields: dict[str, str] | None = None
