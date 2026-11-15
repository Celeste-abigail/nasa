import { useTranslation } from "react-i18next";

import { fmt } from "../../lib/format";
import type { MentalAssessment } from "../../lib/types";

interface Line {
  value: number;
  className: string;
  label: string;
}

function Chart({
  values,
  secondary,
  max,
  lines = [],
  lang,
}: {
  values: number[];
  secondary?: Array<number | null>;
  max: number;
  lines?: Line[];
  lang: string;
}) {
  if (values.length === 0) return null;
  const W = 680;
  const H = 170;
  const L = 44;
  const R = 12;
  const T = 12;
  const B = 24;
  const X = (index: number) =>
    L + (values.length === 1 ? 0 : (index / (values.length - 1)) * (W - L - R));
  const Y = (value: number) => H - B - (value / max) * (H - T - B);

  const secondaryPoints = (secondary ?? [])
    .map((value, index) => (value === null ? null : `${X(index)},${Y(value)}`))
    .filter((point): point is string => point !== null)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mental-series-chart" role="img">
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
        <g key={ratio}>
          <line
            x1={L}
            x2={W - R}
            y1={Y(max * ratio)}
            y2={Y(max * ratio)}
            className="grid"
          />
          <text x={L - 8} y={Y(max * ratio) + 4} textAnchor="end">
            {fmt(max * ratio, lang, 0)}
          </text>
        </g>
      ))}

      {lines.map((line) => (
        <g key={line.label}>
          <line
            x1={L}
            x2={W - R}
            y1={Y(line.value)}
            y2={Y(line.value)}
            className={line.className}
          />
          <text
            x={W - R - 4}
            y={Y(line.value) - 4}
            textAnchor="end"
            className="threshold-label"
          >
            {line.label}
          </text>
        </g>
      ))}

      <polyline
        className="series"
        points={values.map((value, index) => `${X(index)},${Y(value)}`).join(" ")}
      />
      {secondaryPoints && (
        <polyline className="series-secondary" points={secondaryPoints} />
      )}
      {values.map((value, index) => (
        <circle key={index} cx={X(index)} cy={Y(value)} r={3.5} className="dot">
          <title>{fmt(value, lang, 2)}</title>
        </circle>
      ))}
    </svg>
  );
}

export function MentalCharts({
  assessment,
  lang,
}: {
  assessment: MentalAssessment;
  lang: string;
}) {
  const { t } = useTranslation();
  const tlx = assessment.tlx_points;
  const cda = assessment.cda_days;
  const sleep = assessment.sleep_nights;
  const pvt = assessment.pvt_tests;

  return (
    <div className="mental-charts">
      <div>
        <h2>{t("mental.chart.tlx")}</h2>
        <Chart
          values={tlx.map((point) => point.tlx)}
          secondary={tlx.map((point) => point.ewma)}
          max={100}
          lang={lang}
          lines={[
            { value: 49.93, className: "limit p50", label: "P50" },
            { value: 68, className: "limit p90", label: "P90" },
          ]}
        />
      </div>

      <div>
        <h2>{t("mental.chart.cda")}</h2>
        <Chart
          values={cda.map((point) => point.iad)}
          max={100}
          lang={lang}
          lines={[
            { value: 60, className: "limit warn", label: "60" },
            { value: 40, className: "limit bad", label: "40" },
          ]}
        />
      </div>

      <div>
        <h2>{t("mental.chart.sleep")}</h2>
        <Chart
          values={sleep.map((night) => night.tst_min / 60)}
          max={10}
          lang={lang}
          lines={[
            { value: 6, className: "limit warn", label: "6 h" },
            { value: 5, className: "limit bad", label: "5 h" },
          ]}
        />
      </div>

      <div>
        <h2>{t("mental.chart.pvt")}</h2>
        <Chart values={pvt.map((test) => test.speed)} max={5} lang={lang} />
      </div>
    </div>
  );
}
