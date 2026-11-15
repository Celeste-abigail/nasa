import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../../lib/api";
import { fmt } from "../../lib/format";
import type { MentalAssessment } from "../../lib/types";
import { CdaForm } from "./CdaForm";
import { MentalCharts } from "./MentalCharts";
import { PvtTestPanel } from "./PvtTest";
import { SleepForm } from "./SleepForm";
import { TlxForm } from "./TlxForm";

interface Props {
  astronaut: string;
  lang: string;
  onToast: (message: string) => void;
}

function StatusChip({
  label,
  color,
  value,
}: {
  label: string;
  color: number | null | undefined;
  value: string;
}) {
  const { t } = useTranslation();
  return (
    <span className={`badge ${color ? `s${color}` : "s0"}`}>
      {label}: {value}
      {color ? ` · ${t(`mental.status.${color}`)}` : ""}
    </span>
  );
}

export function MentalView({ astronaut, lang, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"forms" | "follow">("forms");

  const query = useQuery({
    queryKey: ["mental", astronaut, lang],
    queryFn: () => api.mental(astronaut, lang),
    enabled: Boolean(astronaut),
  });

  const data: MentalAssessment | undefined = query.data;
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["mental"] });

  const lastTlx = data?.tlx_points.at(-1);
  const lastCda = data?.current_cda;
  const lastSleep = data?.current_sleep;
  const lastPvt = data?.current_pvt;

  return (
    <div>
      <div className="mental-tabs">
        <button
          type="button"
          className={tab === "forms" ? "on" : ""}
          onClick={() => setTab("forms")}
        >
          <i className="fa-solid fa-clipboard-list" aria-hidden="true" />
          {t("mental.tab.forms")}
        </button>
        <button
          type="button"
          className={tab === "follow" ? "on" : ""}
          onClick={() => setTab("follow")}
        >
          <i className="fa-solid fa-chart-line" aria-hidden="true" />
          {t("mental.tab.follow")}
        </button>
      </div>

      {query.isLoading && <div className="empty">{t("common.loading")}</div>}
      {query.isError && (
        <section className="panel">
          <p className="err">{t("common.error")}</p>
          <button type="button" onClick={() => void query.refetch()}>
            {t("common.retry")}
          </button>
        </section>
      )}

      {data && tab === "forms" && (
        <div className="questionnaire-grid">
          <TlxForm
            astronaut={astronaut}
            lang={lang}
            onSaved={() => void refresh()}
            onToast={onToast}
          />
          <CdaForm
            astronaut={astronaut}
            lang={lang}
            onSaved={() => void refresh()}
            onToast={onToast}
          />
          <SleepForm
            astronaut={astronaut}
            lang={lang}
            profile={data.sleep_profile}
            onSaved={() => void refresh()}
            onToast={onToast}
          />
          <PvtTestPanel
            astronaut={astronaut}
            lang={lang}
            onSaved={() => void refresh()}
            onToast={onToast}
          />
        </div>
      )}

      {data && tab === "follow" && (
        <section className="panel main">
          <div className="mental-summary">
              <StatusChip
                label="NASA-TLX"
                color={lastTlx?.color}
                value={data.current_tlx ? fmt(data.current_tlx.tlx, lang, 1) : "—"}
              />
              <StatusChip
                label="IAD"
                color={lastCda?.color}
                value={lastCda ? fmt(lastCda.iad, lang, 1) : "—"}
              />
              <StatusChip
                label="TST"
                color={lastSleep?.color}
                value={lastSleep ? `${fmt(lastSleep.tst_min / 60, lang, 1)} h` : "—"}
              />
              <StatusChip
                label="PVT"
                color={lastPvt?.color ?? null}
                value={lastPvt ? fmt(lastPvt.speed, lang, 2) : "—"}
              />
              <span className={`badge ${data.global_color ? `s${data.global_color}` : "s0"}`}>
                {data.global_color
                  ? t(`mental.status.${data.global_color}`)
                  : t("mental.status.none")}
              </span>
            </div>

            <MentalCharts assessment={data} lang={lang} />

            <div>
              <h2>{t("mental.prescriptions.title")}</h2>
              {data.prescriptions.length === 0 ? (
                <div className="empty">{t("mental.prescriptions.none")}</div>
              ) : (
                <div className="prescription-grid">
                  {data.prescriptions.map((item) => (
                    <article
                      key={item.id}
                      className={`prescription-card s${item.severity}`}
                    >
                      <div className="prescription-head">
                        <b>{item.id}</b>
                        <span className="badge">{t(`mental.status.${item.severity}`)}</span>
                      </div>
                      <h3>{t(`mental.${item.id.toLowerCase()}.title`)}</h3>
                      <p>{t(`mental.${item.id.toLowerCase()}.body`)}</p>
                      <p className="prescription-action">
                        <i className="fa-solid fa-arrow-right" aria-hidden="true" />
                        {t(`mental.${item.id.toLowerCase()}.action`)}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2>{t("mental.adherence.title")}</h2>
              <div className="cortisol-cards">
                <div className="cortisol-card">
                  <h3>NASA-TLX</h3>
                  <b>
                    {data.adherence.tlx_sessions ?? 0}/{7}
                  </b>
                </div>
                <div className="cortisol-card">
                  <h3>CDA</h3>
                  <b>
                    {data.adherence.cda_days ?? 0}/{7}
                  </b>
                </div>
                <div className="cortisol-card">
                  <h3>{t("mental.chart.sleep")}</h3>
                  <b>
                    {data.adherence.sleep_nights ?? 0}/{7}
                  </b>
                </div>
                <div className="cortisol-card">
                  <h3>PVT</h3>
                  <b>
                    {data.adherence.pvt_tests ?? 0}/{7}
                  </b>
                </div>
              </div>
              <p className="hint">
                {t("mental.sleep.window_suggestion", {
                  current: data.sleep_profile.window_minutes,
                  suggested: data.window_suggestion,
                })}
              </p>
              <p className="hint">
                <i className="fa-solid fa-lock" aria-hidden="true" />{" "}
                {t("mental.privacy.note")}
              </p>
            </div>
          </section>
      )}
    </div>
  );
}
