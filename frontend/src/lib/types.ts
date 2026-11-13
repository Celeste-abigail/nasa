export type Site = "calcaneus" | "femoral_neck";

export interface Astronaut {
  code: string;
  name: string;
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
  warnings: string[];
  model: ModelInfo;
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

export interface ImportRowError {
  line: number;
  message: string;
}

export interface ImportReport {
  created: number;
  skipped: number;
  errors: ImportRowError[];
}
