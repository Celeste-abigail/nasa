import { useTranslation } from "react-i18next";

import { fmt } from "../../lib/format";
import type { Point } from "../../lib/types";

interface Props {
  current: Point | null;
  warnings: string[];
  lang: string;
}

export function StatusPanel({ current, warnings, lang }: Props) {
  const { t } = useTranslation();

  if (!current) {
    return (
      <div className="kpis">
        <div className="empty">{t("common.no_data")}</div>
      </div>
    );
  }

  return (
    <>
      {warnings.length > 0 && (
        <div className="warnings" role="status">
          <strong>{t("monitoring.warning")}:</strong>
          <ul>
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="kpis">
        <div className={`kpi status l${current.level}`}>
          <b>{current.level_name}</b>
          <span>{current.level_tip}</span>
        </div>
        <div className="kpi">
          <b>{fmt(current.cumulative_loss_pct, lang, 1)} %</b>
          <span>{t("monitoring.kpi.cumulative")}</span>
        </div>
        <div className="kpi">
          <b>
            {current.rate_pct_month === null ? "—" : fmt(current.rate_pct_month, lang, 2)}
          </b>
          <span>{t("monitoring.kpi.rate")}</span>
        </div>
        <div className="kpi">
          <b>{fmt(current.bv_tv, lang, 3)}</b>
          <span>{t("monitoring.kpi.bvtv")}</span>
        </div>
        <div className="kpi">
          <b>{current.day}</b>
          <span>{t("monitoring.kpi.days")}</span>
        </div>
      </div>
    </>
  );
}
