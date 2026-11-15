export type Severity = 0 | 1 | 2 | 3 | 4;

export type ModuleKey = "bone" | "cortisol" | "radiation" | "mental";

const clamp = (value: number): Severity =>
  Math.min(4, Math.max(0, Math.round(value))) as Severity;

export function boneSeverity(level: number | null | undefined): Severity {
  if (level === null || level === undefined) return 0;
  return clamp(level);
}

export function cortisolSeverity(color: number | null | undefined): Severity {
  if (color === null || color === undefined) return 0;
  return clamp(color);
}

export function radiationSeverity(color: number | null | undefined): Severity {
  if (color === null || color === undefined) return 0;
  return clamp(color);
}

export function mentalSeverity(zone: string | null | undefined): Severity {
  switch (zone) {
    case "green":
      return 1;
    case "yellow":
      return 2;
    case "orange":
      return 3;
    case "red":
      return 4;
    default:
      return 0;
  }
}

export function worst(severities: Severity[]): Severity {
  return severities.reduce<Severity>((max, value) => (value > max ? value : max), 0);
}

export function attentionCount(severities: Severity[]): number {
  return severities.filter((value) => value >= 2).length;
}

export function severityClass(severity: Severity): string {
  return `s${severity}`;
}
