import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { fmt, formatDateTime } from "../../lib/format";
import {
  attentionCount,
  boneSeverity,
  cortisolSeverity,
  mentalSeverity,
  radiationSeverity,
  severityClass,
  worst,
  type ModuleKey,
} from "../../lib/severity";
import type { Site } from "../../lib/types";
import { SummaryCard } from "./SummaryCard";
import { useOverview } from "./useOverview";

interface Props {
  astronaut: string;
  site: Site;
  lang: string;
  onOpen: (view: ModuleKey) => void;
}

const MODULES: ModuleKey[] = ["bone", "cortisol", "radiation", "mental"];
const STORAGE_KEY = "nasa-space-summary";

function readSelection(): ModuleKey[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return MODULES;
    const parsed = JSON.parse(raw) as string[];
    const valid = MODULES.filter((key) => parsed.includes(key));
    return valid.length > 0 ? valid : MODULES;
  } catch {
    return MODULES;
  }
}

export function OverviewView({ astronaut, site, lang, onOpen }: Props) {
  const { t } = useTranslation();
  const { bone, cortisol, radiation, mental } = useOverview(astronaut, site, lang);
  const [selected, setSelected] = useState<ModuleKey[]>(readSelection);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
  }, [selected]);

  function toggle(key: ModuleKey) {
    setSelected((current) => {
      if (current.includes(key)) {
        return current.length === 1 ? current : current.filter((item) => item !== key);
      }
      return MODULES.filter((item) => current.includes(item) || item === key);
    });
  }

  const boneData = bone.data;
  const cortisolData = cortisol.data;
  const radiationData = radiation.data;
  const mentalData = mental.data;

  const severities = [
    boneSeverity(boneData?.current?.level),
    cortisolSeverity(cortisolData?.current?.color),
    radiationSeverity(radiationData?.color),
    mentalSeverity(mentalData?.current?.zone),
  ];
  const worstSeverity = worst(severities);
  const attention = attentionCount(severities);
  const profile = boneData?.astronaut ?? mentalData?.astronaut ?? null;

  return (
    <div>
      <div className="overview-status">
        <span className={`badge ${severityClass(worstSeverity)}`}>
          {t(`overview.severity.${worstSeverity}`)}
        </span>
        <span className="hint">
          {attention > 0
            ? t("overview.attention", { count: attention })
            : t("overview.nominal")}
        </span>
        {profile && (
          <span className="hint">
            {profile.code}
            {profile.age !== null ? ` · ${t("profile.age", { age: profile.age })}` : ""}
            {profile.sex ? ` · ${t(`sex.${profile.sex}`)}` : ""}
          </span>
        )}
      </div>

      <div className="overview-chips" role="group" aria-label={t("overview.filter")}>
        <button
          type="button"
          className={selected.length === MODULES.length ? "on" : ""}
          onClick={() => setSelected(MODULES)}
        >
          {t("overview.all")}
        </button>
        {MODULES.map((key) => (
          <button
            key={key}
            type="button"
            className={selected.includes(key) ? "on" : ""}
            aria-pressed={selected.includes(key)}
            onClick={() => toggle(key)}
          >
            {t(`view.${key}`)}
          </button>
        ))}
      </div>

      {!astronaut ? (
        <section className="panel">
          <div className="empty">{t("common.loading")}</div>
        </section>
      ) : (
        <div className="overview-grid">
          {selected.includes("bone") && (
            <SummaryCard
              title={t("view.bone")}
              icon="fa-bone"
              severity={boneSeverity(boneData?.current?.level)}
              badge={
                boneData?.current
                  ? boneData.current.level_name
                  : t("overview.no_data")
              }
              primary={
                boneData?.current
                  ? fmt(boneData.current.cumulative_loss_pct, lang, 1)
                  : "—"
              }
              unit="%"
              metrics={[
                {
                  label: t("overview.metric.rate"),
                  value: boneData?.current
                    ? `${fmt(boneData.current.rate_pct_month, lang, 2)} %/mes`
                    : "—",
                },
                {
                  label: t("overview.metric.bvtv"),
                  value: boneData?.current
                    ? fmt(boneData.current.bv_tv, lang, 3)
                    : "—",
                },
                {
                  label: t("overview.metric.status"),
                  value: boneData?.current
                    ? t(`bone.${boneData.current.bone_status}`)
                    : "—",
                },
                {
                  label: t("overview.metric.month"),
                  value: boneData?.current
                    ? fmt(boneData.current.month, lang, 1)
                    : "—",
                },
              ]}
              updated={boneData?.current?.measured_on ?? null}
              spark={boneData?.points.map((point) => point.cumulative_loss_pct)}
              onOpen={() => onOpen("bone")}
              loading={bone.isLoading}
              error={bone.isError}
              empty={!boneData?.current}
            />
          )}

          {selected.includes("cortisol") && (
            <SummaryCard
              title={t("view.cortisol")}
              icon="fa-droplet"
              severity={cortisolSeverity(cortisolData?.current?.color)}
              badge={
                cortisolData?.current
                  ? t(`cortisol.color.${cortisolData.current.color}`)
                  : t("overview.no_data")
              }
              primary={
                cortisolData?.current
                  ? fmt(cortisolData.current.value_ug_dl, lang, 2)
                  : "—"
              }
              unit="µg/dL"
              metrics={[
                {
                  label: t("overview.metric.band"),
                  value: cortisolData?.current
                    ? t(`cortisol.band.${cortisolData.current.band}`)
                    : "—",
                },
                {
                  label: t("overview.metric.z"),
                  value: cortisolData?.current
                    ? fmt(cortisolData.current.z, lang, 2)
                    : "—",
                },
                {
                  label: t("overview.metric.ratio"),
                  value: cortisolData?.ratio
                    ? fmt(cortisolData.ratio.ratio, lang, 2)
                    : "—",
                },
                {
                  label: "nmol/L",
                  value: cortisolData?.current
                    ? fmt(cortisolData.current.value_nmol_l, lang, 1)
                    : "—",
                },
              ]}
              updated={
                cortisolData?.current
                  ? formatDateTime(cortisolData.current.measured_at, lang)
                  : null
              }
              spark={cortisolData?.samples.map((sample) => sample.value_ug_dl)}
              onOpen={() => onOpen("cortisol")}
              loading={cortisol.isLoading}
              error={cortisol.isError}
              empty={!cortisolData?.current}
            />
          )}

          {selected.includes("radiation") && (
            <SummaryCard
              title={t("view.radiation")}
              icon="fa-radiation"
              severity={radiationSeverity(radiationData?.color)}
              badge={
                radiationData?.color
                  ? t(`radiation.color.${radiationData.color}`)
                  : t("overview.no_data")
              }
              primary={
                radiationData?.current
                  ? fmt(radiationData.current.eq_rate_usv_min, lang, 2)
                  : "—"
              }
              unit="µSv/min"
              metrics={[
                {
                  label: t("overview.metric.layer_a"),
                  value: radiationData
                    ? t(`radiation.layer.status.${radiationData.layers.a.status}`)
                    : "—",
                },
                {
                  label: t("overview.metric.f30"),
                  value: radiationData
                    ? fmt(radiationData.cumulative.f30, lang, 2)
                    : "—",
                },
                {
                  label: t("overview.metric.fcareer"),
                  value: radiationData
                    ? fmt(radiationData.cumulative.f_career, lang, 2)
                    : "—",
                },
              ]}
              updated={
                radiationData?.current
                  ? formatDateTime(radiationData.current.measured_at, lang)
                  : null
              }
              spark={radiationData?.readings.map((reading) => reading.eq_rate_usv_min)}
              onOpen={() => onOpen("radiation")}
              loading={radiation.isLoading}
              error={radiation.isError}
              empty={!radiationData?.current}
            />
          )}

          {selected.includes("mental") && (
            <SummaryCard
              title={t("view.mental")}
              icon="fa-brain"
              severity={mentalSeverity(mentalData?.current?.zone)}
              badge={
                mentalData?.current
                  ? t(`overview.zone.${mentalData.current.zone}`)
                  : t("overview.no_data")
              }
              primary={
                mentalData?.current
                  ? `ALI ${fmt(mentalData.current.ali, lang, 1)}`
                  : "—"
              }
              metrics={[
                {
                  label: t("overview.metric.dmrs"),
                  value: mentalData?.current
                    ? fmt(mentalData.current.dmrs, lang, 1)
                    : "—",
                },
                {
                  label: t("overview.metric.wl"),
                  value: mentalData?.current
                    ? fmt(mentalData.current.wl_day, lang, 1)
                    : "—",
                },
                {
                  label: t("overview.metric.ewma"),
                  value: mentalData?.current
                    ? fmt(mentalData.current.ewma_mood, lang, 1)
                    : "—",
                },
                {
                  label: t("overview.metric.reasons"),
                  value: mentalData?.current
                    ? mentalData.current.reasons
                        .slice(0, 2)
                        .map((reason) => t(`mental.reason.${reason}`))
                        .join(" · ")
                    : "—",
                },
              ]}
              updated={mentalData?.current?.day ?? null}
              spark={mentalData?.days.map((day) => day.ali)}
              onOpen={() => onOpen("mental")}
              loading={mental.isLoading}
              error={mental.isError}
              empty={!mentalData?.current}
            />
          )}
        </div>
      )}
    </div>
  );
}
