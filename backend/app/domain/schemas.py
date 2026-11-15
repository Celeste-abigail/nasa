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
    month: float
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


class RecommendationOut(BaseModel):
    level: int
    title: str
    items: list[str]
    disclaimer: str


class AssessmentOut(BaseModel):
    astronaut: AstronautOut
    site: Site
    baseline: PointOut | None
    points: list[PointOut]
    current: PointOut | None
    reference: ReferenceOut | None
    recommendations: RecommendationOut
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


# --- Modulo de radiacion (TEPC) ---

Region = Literal["gcr", "saa", "unknown"]


class RadiationReadingCreate(BaseModel):
    measured_at: datetime
    eq_rate: float
    dose_rate: float | None = None
    region: Region = "unknown"
    module: str | None = Field(default=None, max_length=64)
    mission_day: int | None = Field(default=None, ge=0, le=2000)
    planned_days: int | None = Field(default=None, ge=1, le=2000)
    prior_career_msv: float | None = Field(default=None, ge=0, le=1000)
    notes: str | None = Field(default=None, max_length=500)


class RadiationLayerOut(BaseModel):
    color: int | None
    status: str
    value: float | None = None
    p95: float | None = None
    p99: float | None = None
    fraction: float | None = None
    detail: str


class RadiationReadingOut(BaseModel):
    id: int
    measured_at: datetime
    eq_rate_usv_min: float
    dose_rate_ugy_min: float | None
    region: Region
    module: str | None
    mission_day: int | None
    planned_days: int | None
    prior_career_msv: float | None
    notes: str | None
    source: str
    q_factor: float | None


class RadiationCumulativeOut(BaseModel):
    h_30d_msv: float | None
    f30: float | None
    h_total_msv: float | None
    projection_msv: float | None
    f_career: float | None


class RadiationStratumOut(BaseModel):
    region: str
    hour: int | None
    module: str | None
    epoch: str | None


class RadiationReferenceOut(BaseModel):
    source: str
    product: str
    period: dict
    metric: str
    unit: str
    stratum: RadiationStratumOut | None
    used_fallback: bool
    daily_available: bool
    min_cell_n: int
    limits: dict[str, float]
    thresholds: dict[str, float]
    notes: str


class RadiationAssessmentOut(BaseModel):
    astronaut: AstronautOut
    readings: list[RadiationReadingOut]
    current: RadiationReadingOut | None
    layers: dict[str, RadiationLayerOut]
    color: int | None
    cumulative: RadiationCumulativeOut
    reference: RadiationReferenceOut
    warnings: list[str]


# --- Modulo de salud mental (TLX + CDA + sueno + PVT) ---


class TlxComparisonIn(BaseModel):
    pair: list[str]
    choice: str


class TlxSessionCreate(BaseModel):
    taken_at: datetime | None = None
    task_description: str = Field(min_length=3, max_length=300)
    task_category: str = Field(min_length=1, max_length=64)
    duration_min: int | None = Field(default=None, ge=1, le=1440)
    ratings: dict[str, int]
    comparisons: list[TlxComparisonIn]


class TlxSessionOut(BaseModel):
    id: int
    taken_at: datetime
    task_description: str
    task_category: str
    duration_min: int | None
    ratings: dict[str, int]
    counts: dict[str, int]
    weights: dict[str, float]
    contributions: dict[str, float]
    tlx: float
    rtlx: float
    dominant: str


class TlxPointOut(BaseModel):
    index: int
    taken_at: datetime
    tlx: float
    rtlx: float
    dominant: str
    color: int
    phase: str
    z: float | None
    ewma: float | None
    se: float | None
    limit_warn: float | None
    limit_action: float | None
    underload: bool


class CdaInput(BaseModel):
    items: dict[str, int]


class CdaPointOut(BaseModel):
    day: date
    iad: float
    positive: float
    negative: float
    stress_fatigue: float
    sleep: float
    connection: float
    color: int
    phase: str
    mm7: float | None
    z: float | None
    flags: list[str]


class SleepProfileIn(BaseModel):
    need_hours: float = Field(default=7.5, ge=4, le=12)
    scheduled_wake: str = Field(default="06:00", pattern=r"^\d{2}:\d{2}$")
    window_minutes: int = Field(default=450, ge=240, le=720)
    blocked: bool = False


class SleepProfileOut(BaseModel):
    need_hours: float
    scheduled_wake: str
    window_minutes: int
    last_adjustment: date | None
    blocked: bool


class SleepNightIn(BaseModel):
    day: date
    entry_at: datetime
    latency_min: int = Field(ge=0, le=240)
    awakenings: int = Field(ge=0, le=20)
    waso_min: int = Field(ge=0, le=600)
    cause_group: Literal["A", "B"] | None = None
    cause_detail: str | None = Field(default=None, max_length=64)
    final_wake_at: datetime
    exit_at: datetime
    quality: int = Field(ge=0, le=10)
    inertia: int = Field(ge=0, le=10)
    dreams: Literal["none", "neutral", "vivid", "nightmare"] = "none"
    environmental: list[str] = Field(default_factory=list)
    nap_min: int | None = Field(default=None, ge=0, le=600)


class SleepNightOut(BaseModel):
    day: date
    entry_at: datetime
    final_wake_at: datetime
    exit_at: datetime
    latency_min: int
    awakenings: int
    waso_min: int
    cause_group: str | None
    cause_detail: str | None
    quality: int
    inertia: int
    dreams: str
    environmental: list[str]
    nap_min: int | None
    tib_min: float
    tst_min: float
    efficiency: float
    midpoint_at: datetime
    color: int
    flags: list[str]
    debt_hours: float
    se7: float | None
    midpoint_shift_min: float | None
    excluded: bool


class PvtInput(BaseModel):
    taken_at: datetime | None = None
    mode: Literal[60, 180] = 60
    trials: list[int]
    false_starts: int = Field(default=0, ge=0, le=1000)
    subjective_alertness: int | None = Field(default=None, ge=0, le=10)


class PvtOut(BaseModel):
    id: int
    taken_at: datetime
    mode: int
    valid_count: int
    lapses: int
    false_starts: int
    mean_rt_ms: float
    speed: float
    subjective_alertness: int | None
    z: float | None
    color: int | None
    discrepancy: bool


class PrescriptionOut(BaseModel):
    id: str
    severity: int


class MentalAssessmentOut(BaseModel):
    astronaut: AstronautOut
    tlx_points: list[TlxPointOut]
    cda_days: list[CdaPointOut]
    sleep_nights: list[SleepNightOut]
    pvt_tests: list[PvtOut]
    current_tlx: TlxSessionOut | None
    current_cda: CdaPointOut | None
    current_sleep: SleepNightOut | None
    current_pvt: PvtOut | None
    global_color: int | None
    prescriptions: list[PrescriptionOut]
    sleep_profile: SleepProfileOut
    window_suggestion: int
    adherence: dict[str, int]
    privacy: dict[str, bool]
    thresholds: dict[str, float]
    warnings: list[str]


class MetaOut(BaseModel):
    app_name: str
    model: ModelInfo
    sites: list[str]
    languages: list[str]
    thresholds: dict[str, float]
    units: dict[str, str]
    reference: ReferenceInfoOut
    cortisol: CortisolReferenceOut
    radiation: RadiationReferenceOut


class ErrorBody(BaseModel):
    detail: str
    code: str | None = None
    fields: dict[str, str] | None = None
