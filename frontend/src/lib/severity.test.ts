import { describe, expect, it } from "vitest";

import {
  attentionCount,
  boneSeverity,
  cortisolSeverity,
  mentalSeverity,
  radiationSeverity,
  severityClass,
  worst,
} from "./severity";

describe("severity", () => {
  it("mapea cada modulo a 0-4", () => {
    expect(boneSeverity(null)).toBe(0);
    expect(boneSeverity(1)).toBe(1);
    expect(boneSeverity(3)).toBe(3);
    expect(cortisolSeverity(2)).toBe(2);
    expect(radiationSeverity(3)).toBe(3);
    expect(radiationSeverity(null)).toBe(0);
  });

  it("mapea las zonas mentales", () => {
    expect(mentalSeverity("green")).toBe(1);
    expect(mentalSeverity("yellow")).toBe(2);
    expect(mentalSeverity("orange")).toBe(3);
    expect(mentalSeverity("red")).toBe(4);
    expect(mentalSeverity(undefined)).toBe(0);
  });

  it("calcula el peor estado y el conteo de atencion", () => {
    expect(worst([0, 1, 2, 3])).toBe(3);
    expect(worst([0, 0])).toBe(0);
    expect(worst([])).toBe(0);
    expect(attentionCount([1, 2, 3, 0])).toBe(2);
    expect(attentionCount([1, 1])).toBe(0);
  });

  it("genera la clase css de severidad", () => {
    expect(severityClass(0)).toBe("s0");
    expect(severityClass(4)).toBe("s4");
  });
});
