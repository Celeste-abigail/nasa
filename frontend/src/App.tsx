import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "./lib/api";
import { CortisolView } from "./modules/cortisol/CortisolView";
import { CrewManager } from "./modules/crew/CrewManager";
import { ImportPanel } from "./modules/measurements/ImportPanel";
import { ProfilePanel } from "./modules/measurements/ProfilePanel";
import { RegisterPanel } from "./modules/measurements/RegisterPanel";
import { HistoryTable } from "./modules/monitoring/HistoryTable";
import { MentalView } from "./modules/mental/MentalView";
import { OverviewView } from "./modules/overview/OverviewView";
import { RecommendationsPanel } from "./modules/monitoring/RecommendationsPanel";
import { RadiationView } from "./modules/radiation/RadiationView";
import { StatusPanel } from "./modules/monitoring/StatusPanel";
import { TrendChart } from "./modules/monitoring/TrendChart";
import { Header } from "./modules/shell/Header";
import { useToast } from "./modules/shell/Toast";

type View = "overview" | "bone" | "cortisol" | "radiation" | "mental";

const MODULE_SCIENTIFIC_FOOTERS: Record<
  Exclude<View, "overview">,
  { formula: string; dois: string[] }
> = {
  bone: {
    formula: "BV/TV = 3.89e-4 * UV - 9e-4 * BUA - 0.456",
    dois: [
      "https://doi.org/10.1117/12.810048",
      "https://doi.org/10.1016/j.actaastro.2012.08.032",
      "https://doi.org/10.1121/1.4784949",
    ],
  },
  cortisol: {
    formula: "z = (ln(value) - ln(median(t))) / σ_ln · CLIA/ECLIA Circadian Model",
    dois: [
      "https://doi.org/10.1016/j.psyneuen.2012.04.019",
      "https://doi.org/10.1515/cclm-2006-0458",
      "https://doi.org/10.1038/s41526-018-0041-4",
    ],
  },
  radiation: {
    formula: "F30 = H30 / 250 mSv · F_career = H_total / 600 mSv · ISS TEPC A/B/C",
    dois: [
      "https://doi.org/10.1016/j.lssr.2020.04.001",
      "https://doi.org/10.1667/RR1889.1",
      "https://doi.org/10.1029/2009SW000492",
    ],
  },
  mental: {
    formula: "NASA-TLX · DMRS (IAD) · Sleep Architecture (SE/SRI) · PVT-B",
    dois: [
      "https://doi.org/10.1016/S0166-4115(08)62386-9",
      "https://doi.org/10.1177/1541931215591373",
      "https://doi.org/10.5665/sleep.1158",
    ],
  },
};

export default function App() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "en";
  const queryClient = useQueryClient();
  const { message, show } = useToast();

  const [astronaut, setAstronaut] = useState("");
  const [crewOpen, setCrewOpen] = useState(false);
  const [view, setView] = useState<View>(() => {
    const hash = window.location.hash.replace("#", "");
    return hash === "bone" ||
      hash === "cortisol" ||
      hash === "radiation" ||
      hash === "mental"
      ? hash
      : "overview";
  });

  useEffect(() => {
    const target = view === "overview" ? "" : `#${view}`;
    const current = window.location.hash;
    if (current !== target) {
      history.replaceState(
        null,
        "",
        `${window.location.pathname}${window.location.search}${target}`
      );
    }
  }, [view]);

  const metaQuery = useQuery({
    queryKey: ["meta", lang],
    queryFn: () => api.meta(lang),
  });

  const astronautsQuery = useQuery({
    queryKey: ["astronauts", lang],
    queryFn: () => api.astronauts(lang),
  });

  const astronauts = astronautsQuery.data ?? [];
  const active = astronaut || astronauts[0]?.code || "";

  const assessmentQuery = useQuery({
    queryKey: ["monitoring", active, lang],
    queryFn: () => api.monitoring(active, "calcaneus", lang),
    enabled: active !== "",
  });

  useEffect(() => {
    if (!astronaut && astronauts.length > 0) {
      setAstronaut(astronauts[0].code);
    }
  }, [astronaut, astronauts]);

  useEffect(() => {
    if (
      astronauts.length > 0 &&
      !astronauts.some((item) => item.code === active)
    ) {
      setAstronaut(astronauts[0].code);
    }
  }, [active, astronauts]);

  const meta = metaQuery.data;
  const assessment = assessmentQuery.data;
  const profile = astronauts.find((item) => item.code === active) ?? null;
  const loadError =
    metaQuery.isError || astronautsQuery.isError || assessmentQuery.isError;

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["monitoring"] });
  }

  const activeFooter =
    view !== "overview"
      ? {
          formula:
            view === "bone" && meta?.model.formula
              ? meta.model.formula
              : MODULE_SCIENTIFIC_FOOTERS[view].formula,
          dois:
            view === "bone" && assessment?.model.references?.length
              ? assessment.model.references
              : MODULE_SCIENTIFIC_FOOTERS[view].dois,
        }
      : null;

  return (
    <div className="app">
      <Header
        astronauts={astronauts}
        astronaut={active}
        onAstronaut={setAstronaut}
        lang={lang}
        onLang={(next) => void i18n.changeLanguage(next)}
        modelVersion={meta?.model.version}
        view={view}
        onView={setView}
        onCrew={() => setCrewOpen(true)}
      />

      {view !== "overview" && (
        <div className="detail-bar">
          <button
            type="button"
            className="back-btn"
            onClick={() => setView("overview")}
          >
            <i className="fa-solid fa-arrow-left" aria-hidden="true" />
            {t("overview.back")}
          </button>
        </div>
      )}

      {view === "overview" ? (
        <OverviewView astronaut={active} lang={lang} onOpen={setView} />
      ) : view === "cortisol" ? (
        active ? (
          <CortisolView astronaut={active} lang={lang} onToast={show} />
        ) : (
          <section className="panel">
            <div className="empty">{t("common.loading")}</div>
          </section>
        )
      ) : view === "radiation" ? (
        active ? (
          <RadiationView astronaut={active} lang={lang} onToast={show} />
        ) : (
          <section className="panel">
            <div className="empty">{t("common.loading")}</div>
          </section>
        )
      ) : view === "mental" ? (
        active ? (
          <MentalView astronaut={active} lang={lang} onToast={show} />
        ) : (
          <section className="panel">
            <div className="empty">{t("common.loading")}</div>
          </section>
        )
      ) : loadError ? (
        <section className="panel">
          <p className="err">{t("common.error")}</p>
          <button
            type="button"
            onClick={() => {
              void metaQuery.refetch();
              void astronautsQuery.refetch();
              void assessmentQuery.refetch();
            }}
          >
            {t("common.retry")}
          </button>
        </section>
      ) : (
        <div className="shell">
          <div className="column">
            {meta && (
              <RegisterPanel
                key={active}
                astronaut={active}
                meta={meta}
                baselineDate={assessment?.baseline?.measured_on ?? null}
                lastDate={assessment?.points.at(-1)?.measured_on ?? null}
                onSaved={() => {
                  void refresh();
                  show(t("register.saved"));
                }}
              />
            )}
            {meta && (
              <ImportPanel
                astronaut={active}
                lang={lang}
                onImported={() => void refresh()}
                onToast={show}
              />
            )}
            {profile && (
              <ProfilePanel
                key={`profile-${profile.code}`}
                astronaut={profile}
                lang={lang}
                onToast={show}
                onSaved={() => {
                  void queryClient.invalidateQueries({
                    queryKey: ["astronauts"],
                  });
                  void refresh();
                }}
              />
            )}
          </div>

          <section className="panel main" aria-labelledby="monitoring-title">
            <div>
              <h2 id="monitoring-title">{t("monitoring.title")}</h2>
              <StatusPanel
                current={assessment?.current ?? null}
                reference={assessment?.reference ?? null}
                warnings={assessment?.warnings ?? []}
                lang={lang}
              />
            </div>

            <div>
              <h2>{t("chart.title")}</h2>
              {meta && (
                <div className="legend">
                  <span>
                    <i className="swatch ok" />
                    {t("monitoring.legend.normal", {
                      value: meta.thresholds.risk_rate,
                    })}
                  </span>
                  <span>
                    <i className="swatch warn" />
                    {t("monitoring.legend.risk", {
                      min: meta.thresholds.risk_rate,
                      max: meta.thresholds.alert_rate,
                    })}
                  </span>
                  <span>
                    <i className="swatch bad" />
                    {t("monitoring.legend.alert", {
                      rate: meta.thresholds.alert_rate,
                      cumulative: meta.thresholds.alert_cumulative,
                    })}
                  </span>
                </div>
              )}
              <TrendChart
                points={assessment?.points ?? []}
                thresholds={meta?.thresholds}
                lang={lang}
              />
            </div>

            {assessment && (
              <RecommendationsPanel
                recommendation={assessment.recommendations}
              />
            )}

            <div>
              <h2>{t("table.title")}</h2>
              <HistoryTable points={assessment?.points ?? []} lang={lang} />
            </div>
          </section>
        </div>
      )}

      {activeFooter && (
        <footer className="footer labquip-doi-footer">
          <span>{activeFooter.formula}</span>
          {activeFooter.dois.map((reference) => (
            <a
              key={reference}
              href={reference}
              target="_blank"
              rel="noreferrer"
            >
              {reference.replace("https://doi.org/", "DOI ")}
            </a>
          ))}
        </footer>
      )}

      <div className={`toast ${message ? "show" : ""}`} role="status">
        {message}
      </div>

      <CrewManager
        open={crewOpen}
        onClose={() => setCrewOpen(false)}
        active={active}
        onSelect={setAstronaut}
        lang={lang}
        onToast={show}
      />
    </div>
  );
}