import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "../../lib/api";
import { fmt } from "../../lib/format";
import { CortisolChart } from "./CortisolChart";
import { CortisolForm } from "./CortisolForm";
import { CortisolHistory } from "./CortisolHistory";
import { CortisolImport } from "./CortisolImport";
import { CortisolResult } from "./CortisolResult";
import { RecommendationPanel } from "../shell/RecommendationPanel";

interface Props {
  astronaut: string;
  lang: string;
  onToast: (message: string) => void;
}

export function CortisolView({ astronaut, lang, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["cortisol", astronaut, lang],
    queryFn: () => api.cortisol(astronaut, lang),
    enabled: Boolean(astronaut),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["cortisol"] });
  const data = query.data;
  const recColor = data?.current?.color ?? 0;
  const recItems =
    recColor === 3
      ? [
          t("recommendations.cortisol.3.1"),
          t("recommendations.cortisol.3.2"),
          t("recommendations.cortisol.3.3"),
        ]
      : recColor === 2
        ? [t("recommendations.cortisol.2.1"), t("recommendations.cortisol.2.2")]
        : recColor === 1
          ? [t("recommendations.cortisol.1.1"), t("recommendations.cortisol.1.2")]
          : [t("recommendations.cortisol.0.1")];

  return (
    <div className="shell">
      <div className="column">
        <CortisolForm
          astronaut={astronaut}
          lang={lang}
          onSaved={() => void refresh()}
          onToast={onToast}
        />
        <CortisolImport
          astronaut={astronaut}
          lang={lang}
          onImported={() => void refresh()}
          onToast={onToast}
        />
      </div>

      <section className="panel main" aria-labelledby="cortisol-title">
        <div>
          <h2 id="cortisol-title">
            {t("cortisol.title")} <small className="subtitle">{t("cortisol.subtitle")}</small>
          </h2>

          {query.isLoading && <div className="empty">{t("common.loading")}</div>}
          {query.isError && (
            <>
              <p className="err">{t("common.error")}</p>
              <button type="button" onClick={() => void query.refetch()}>
                {t("common.retry")}
              </button>
            </>
          )}

          {data && !data.current && (
            <div className="kpis">
              <div className="empty">{t("cortisol.empty")}</div>
            </div>
          )}

          {data?.current && <CortisolResult current={data.current} lang={lang} />}
        </div>

        {data && (
          <div>
            <h2>{t("cortisol.chart.x")}</h2>
            <CortisolChart curve={data.reference.curve} samples={data.samples} />
          </div>
        )}

        {data && (
          <RecommendationPanel
            severity={recColor}
            title={t("recommendations.cortisol.title")}
            items={recItems}
            note={t("recommendations.cortisol.note")}
            badge={t(`cortisol.color.${recColor || 1}`)}
          />
        )}

        {data && (
          <div className="cortisol-cards">
            <div className="cortisol-card">
              <h3>{t("cortisol.ratio.title")}</h3>
              {data.ratio ? (
                <>
                  <b>{t("cortisol.ratio.value", { ratio: fmt(data.ratio.ratio, lang, 2) })}</b>
                  <span>{t(`cortisol.ratio.${data.ratio.reading}`)}</span>
                </>
              ) : (
                <span>{t("cortisol.ratio.empty")}</span>
              )}
            </div>

            <div className="cortisol-card">
              <h3>
                {data.personal_baseline
                  ? t("cortisol.baseline.title", {
                      band: t(`cortisol.band.${data.personal_baseline.band}`),
                    })
                  : t("cortisol.baseline.title_plain")}
              </h3>
              {data.personal_baseline ? (
                <>
                  <b>
                    {t("cortisol.baseline.text", {
                      n: data.personal_baseline.n,
                      median: fmt(data.personal_baseline.median_ug_dl, lang, 2),
                    })}
                  </b>
                  {data.personal_baseline.delta_pct !== null && (
                    <span>
                      {t("cortisol.baseline.delta", {
                        delta: fmt(data.personal_baseline.delta_pct, lang, 1),
                      })}
                    </span>
                  )}
                </>
              ) : (
                <span>{t("cortisol.baseline.empty")}</span>
              )}
            </div>

            <div className={`cortisol-card ${data.bone_cross_risk ? "warn" : ""}`}>
              <h3>{t("cortisol.cross.title")}</h3>
              <span>{t("cortisol.cross.text")}</span>
            </div>
          </div>
        )}

        {data && (
          <div>
            <h2>{t("cortisol.history.title")}</h2>
            <CortisolHistory samples={data.samples} lang={lang} />
            <p className="hint">
              {t("cortisol.reference", {
                method: data.reference.method,
                source: data.reference.source,
              })}
              {" · "}
              {t("cortisol.age_range", {
                min: data.reference.age_range[0],
                max: data.reference.age_range[1],
              })}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
