export type Site = "calcaneus" | "femoral_neck";
export type Sex = "male" | "female";
export type BoneStatus = "normal" | "osteopenia" | "osteoporosis" | "unknown";

export interface Astronaut {
  code: string;
  name: string;
  sex: Sex | null;
  birth_date: string | null;
  age: number | null;
}

export interface ReferenceMetric {
  mean: number;
  sd: number;
  z: number | null;
  t: number | null;
  status: BoneStatus;
}

export interface Reference {
  sex: Sex;
  age: number;
  age_band: string;
  n: number;
  clamped: boolean;
  source: string;
  population: string;
  bua: ReferenceMetric;
  sos: ReferenceMetric;
  status: BoneStatus;
}

export interface Point {
  measured_on: string;
  day: number;
  bua: number;
  uv: number;
  att: number | null;
  bv_tv: number;
  cumulative_loss_pct: number;
  rate_pct_month: number | null;
  bv_tv_cumulative_loss_pct: number;
  level: 1 | 2 | 3;
  level_name: string;
  level_tip: string;
  bua_z: number | null;
  sos_z: number | null;
  bua_t: number | null;
  sos_t: number | null;
  bone_status: BoneStatus;
}

export interface ModelInfo {
  version: string;
  formula: string;
  references: string[];
}

export interface Assessment {
  astronaut: Astronaut;
  site: Site;
  baseline: Point | null;
  points: Point[];
  current: Point | null;
  reference: Reference | null;
  warnings: string[];
  model: ModelInfo;
}

export interface ReferenceInfo {
  source: string;
  population: string;
  bua_unit: string;
  sos_unit: string;
  age_bands: string[];
  t_thresholds: { osteopenia: number; osteoporosis: number };
}

export interface Meta {
  app_name: string;
  model: ModelInfo;
  sites: Site[];
  languages: string[];
  thresholds: {
    risk_rate: number;
    alert_rate: number;
    alert_cumulative: number;
    bua_min: number;
    bua_max: number;
    uv_min: number;
    uv_max: number;
    att_min: number;
    att_max: number;
  };
  units: { bua: string; uv: string; att: string };
  reference: ReferenceInfo;
  cortisol: CortisolReference;
}

export interface MeasurementInput {
  measured_on: string;
  site: Site;
  bua: number;
  uv: number;
  att: number | null;
}

export interface Measurement {
  id: number;
  measured_on: string;
  site: Site;
  bua: number;
  uv: number;
  att: number | null;
  source: string;
}

export interface AstronautPatch {
  name?: string;
  sex?: Sex;
  birth_date?: string;
}

export interface ImportRowError {
  line: number;
  message: string;
}

export interface ImportReport {
  created: number;
  skipped: number;
  errors: ImportRowError[];
}

// --- Cortisol (modulo independiente) ---

export type CortisolUnit = "ug_dl" | "nmol_l";
export type MissionPhase = "preflight" | "inflight" | "postflight" | "analog";
export type CortisolReading = "normal" | "watch" | "elevated" | "flat";

export interface CortisolSample {
  id: number;
  measured_at: string;
  value_ug_dl: number;
  value_nmol_l: number;
  hour: number;
  band: string;
  z: number;
  percentile: number;
  color: 1 | 2 | 3;
  expected_median_ug_dl: number;
  expected_median_nmol_l: number;
  direction: "high" | "low";
  sex_color: number;
  discordant: boolean;
  above_manufacturer_p95: boolean;
  flags: string[];
  wake_time: string | null;
  mission_phase: MissionPhase | null;
  notes: string | null;
}

export interface CortisolRatio {
  date: string;
  ratio: number;
  reading: CortisolReading;
  afternoon_ug_dl: number;
  night_ug_dl: number;
}

export interface CortisolBaseline {
  band: string;
  n: number;
  median_ug_dl: number;
  delta_pct: number | null;
}

export interface CortisolCurvePoint {
  hour: number;
  median_ug_dl: number;
  p10_ug_dl: number;
  p90_ug_dl: number;
}

export interface CortisolReference {
  method: string;
  source: string;
  sigma_ln: number;
  green_z: number;
  yellow_z: number;
  conversion_nmol_per_ug: number;
  age_range: number[];
  curve: CortisolCurvePoint[];
}

export interface CortisolAssessment {
  astronaut: Astronaut;
  samples: CortisolSample[];
  current: CortisolSample | null;
  ratio: CortisolRatio | null;
  personal_baseline: CortisolBaseline | null;
  bone_cross_risk: boolean;
  warnings: string[];
  reference: CortisolReference;
}

export interface CortisolSampleInput {
  measured_at: string;
  value: number;
  unit: CortisolUnit;
  wake_time?: string | null;
  mission_phase?: MissionPhase | null;
  notes?: string | null;
}
