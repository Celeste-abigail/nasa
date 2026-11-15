import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { severityClass, type Severity } from "../../lib/severity";

interface Props {
  title: string;
  icon: string;
  severity: Severity;
  badge: string;
  primary: string;
  unit?: string;
  metrics: Array<{ label: string; value: ReactNode }>;
  updated?: string | null;
  spark?: number[];
  onOpen: () => void;
  loading?: boolean;
  error?: boolean;
  empty?: boolean;
  emptyLabel?: string;
}

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const width = 200;
  const height = 36;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="sparkline"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polyline points={points} />
    </svg>
  );
}

export function SummaryCard({
  title,
  icon,
  severity,
  badge,
  primary,
  unit,
  metrics,
  updated,
  spark,
  onOpen,
  loading,
  error,
  empty,
  emptyLabel,
}: Props) {
  const { t } = useTranslation();
  const className = `summary-card ${severityClass(severity)}${empty ? " is-empty" : ""}`;

  return (
    <article
      className={className}
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen();
        }
      }}
    >
      <div className="summary-head">
        <div className="summary-heading">
          <span className="summary-icon" aria-hidden="true">
            <i className={`fa-solid ${icon}`} />
          </span>
          <span className="summary-title">{title}</span>
        </div>
        <span className="badge">{badge}</span>
      </div>

      {loading && <div className="empty summary-loading">{t("common.loading")}</div>}
      {error && !loading && <div className="empty summary-loading">{t("overview.unavailable")}</div>}

      {!loading && !error && (
        <>
          <div className="summary-primary">
            {empty ? "—" : primary}
            {!empty && unit ? <small>{unit}</small> : null}
          </div>

          {empty ? (
            <p className="hint">{emptyLabel ?? t("overview.no_data")}</p>
          ) : (
            <div className="summary-metrics">
              {metrics.map((metric) => (
                <div key={metric.label}>
                  <span>{metric.label}</span>
                  <b>{metric.value}</b>
                </div>
              ))}
            </div>
          )}

          {!empty && spark && <Sparkline values={spark} />}

          <div className="summary-footer">
            <span>
              {updated
                ? t("overview.updated", { date: updated })
                : t("overview.no_data")}
            </span>
            <span className="summary-open">{t("overview.open")} →</span>
          </div>
        </>
      )}
    </article>
  );
}
