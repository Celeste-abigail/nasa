import { useTranslation } from "react-i18next";

import type { Astronaut, Site } from "../../lib/types";

interface Props {
  astronauts: Astronaut[];
  astronaut: string;
  onAstronaut: (code: string) => void;
  site: Site;
  onSite: (site: Site) => void;
  lang: string;
  onLang: (lang: string) => void;
  modelVersion?: string;
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
}: Props) {
  const { t } = useTranslation();

  return (
    <header>
      <h1>
        {t("app.title")}
        <small>{t("app.subtitle")}</small>
      </h1>

      <div className="toolbar">
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
      </div>

      {modelVersion ? (
        <p className="model-tag">{t("header.model", { version: modelVersion })}</p>
      ) : null}
    </header>
  );
}
