import { useTranslation } from "react-i18next";

import type { Astronaut } from "../../lib/types";

type View = "overview" | "bone" | "cortisol" | "radiation" | "mental";

interface Props {
  astronauts: Astronaut[];
  astronaut: string;
  onAstronaut: (code: string) => void;
  lang: string;
  onLang: (lang: string) => void;
  modelVersion?: string;
  view: View;
  onView: (view: View) => void;
  onCrew: () => void;
}

export function Header({
  astronauts,
  astronaut,
  onAstronaut,
  lang,
  onLang,
  view,
  onView,
  onCrew,
}: Props) {
  const { t } = useTranslation();

  const tabs: Array<{ key: View; icon: string; label: string }> = [
    { key: "overview", icon: "fa-compass", label: t("view.overview") },
    { key: "bone", icon: "fa-bone", label: t("view.bone") },
    { key: "cortisol", icon: "fa-droplet", label: t("view.cortisol") },
    { key: "radiation", icon: "fa-radiation", label: t("view.radiation") },
    { key: "mental", icon: "fa-brain", label: t("view.mental") },
  ];

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:ital,wght@0,600;0,700;1,600&family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap"
      />
      <header className="labquip-header">
        <div className="labquip-brand-wrap">
          <button
            type="button"
            className="labquip-badge-logo"
            onClick={() => onView("overview")}
          >
            <i className="fa-solid fa-satellite" aria-hidden="true" />
            <span>LABQUIP.APP</span>
          </button>

          <div className="labquip-inline-controls">
            <label className="sr-only" htmlFor="astronaut">
              {t("header.astronaut")}
            </label>
            <select
              id="astronaut"
              className="compact-select"
              value={astronaut}
              onChange={(event) => onAstronaut(event.target.value)}
              title={t("header.astronaut")}
            >
              {astronauts.map((item) => (
                <option key={item.code} value={item.code}>
                  👨‍🚀 {item.code}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="labquip-right-bar">
          <nav className="labquip-nav">
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

          <button
            type="button"
            className="compact-crew"
            onClick={onCrew}
            title={t("crew.manage")}
          >
            <i className="fa-solid fa-users" aria-hidden="true" />
            <span>{t("crew.manage")}</span>
          </button>

          <div
            className="compact-lang"
            role="group"
            aria-label={t("header.language")}
          >
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
      </header>
    </>
  );
}
