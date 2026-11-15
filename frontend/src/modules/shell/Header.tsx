import { useTranslation } from "react-i18next";

import type { Astronaut, Site } from "../../lib/types";

type View = "overview" | "bone" | "cortisol" | "radiation" | "mental";

interface Props {
  astronauts: Astronaut[];
  astronaut: string;
  onAstronaut: (code: string) => void;
  site: Site;
  onSite: (site: Site) => void;
  lang: string;
  onLang: (lang: string) => void;
  modelVersion?: string;
  view: View;
  onView: (view: View) => void;
}

export function Header({
  astronauts,
  astronaut,
  onAstronaut,
  site,
  onSite,
  lang,
  onLang,
  modelVersion,
  view,
  onView,
}: Props) {
  const { t } = useTranslation();

  const tabs: Array<{ key: View; icon: string; label: string }> = [
    { key: "overview", icon: "fa-gauge-high", label: t("view.overview") },
    { key: "bone", icon: "fa-bone", label: t("view.bone") },
    { key: "cortisol", icon: "fa-droplet", label: t("view.cortisol") },
    { key: "radiation", icon: "fa-radiation", label: t("view.radiation") },
    { key: "mental", icon: "fa-brain", label: t("view.mental") },
  ];

  return (
    <header>
      <div className="brand">
        <span className="brand-icon" aria-hidden="true">
          <i className="fa-solid fa-rocket" />
        </span>
        <div>
          <h1>Astro Health Monitor</h1>
          <small>NASA SPACE · SCAN</small>
        </div>
      </div>

      <nav>
        <div className="view-tabs" role="group" aria-label={t("app.title")}>
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={view === tab.key ? "on" : ""}
              aria-pressed={view === tab.key}
              onClick={() => onView(tab.key)}
            >
              <i className={`fa-solid ${tab.icon}`} aria-hidden="true" />
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <div className="header-controls">
        <div className="toolbar-field">
          <label htmlFor="astronaut">{t("header.astronaut")}</label>
          <select
            id="astronaut"
            value={astronaut}
            onChange={(event) => onAstronaut(event.target.value)}
          >
            {astronauts.map((item) => (
              <option key={item.code} value={item.code}>
                {item.code}
              </option>
            ))}
          </select>
        </div>

        <div className="toolbar-field">
          <label htmlFor="site">{t("header.site")}</label>
          <select
            id="site"
            value={site}
            onChange={(event) => onSite(event.target.value as Site)}
          >
            <option value="calcaneus">{t("site.calcaneus")}</option>
            <option value="femoral_neck">{t("site.femoral_neck")}</option>
          </select>
        </div>

        <div className="toolbar-field lang">
          <label>{t("header.language")}</label>
          <div className="segmented" role="group" aria-label={t("header.language")}>
            <button
              type="button"
              className={lang === "es" ? "on" : ""}
              aria-pressed={lang === "es"}
              onClick={() => onLang("es")}
            >
              ES
            </button>
            <button
              type="button"
              className={lang === "en" ? "on" : ""}
              aria-pressed={lang === "en"}
              onClick={() => onLang("en")}
            >
              EN
            </button>
          </div>
        </div>

        {modelVersion ? (
          <p className="model-tag">{t("header.model", { version: modelVersion })}</p>
        ) : null}
      </div>
    </header>
  );
}
