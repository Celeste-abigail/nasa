import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { fmt, formatDateTime } from "../../lib/format";
import {
  attentionCount,
  boneSeverity,
  cortisolSeverity,
  radiationSeverity,
  worst,
  type ModuleKey,
} from "../../lib/severity";
import { SummaryCard } from "./SummaryCard";
import { useOverview } from "./useOverview";

interface Props {
  astronaut: string;
  lang: string;
  onOpen: (view: ModuleKey) => void;
}

const MODULES: ModuleKey[] = ["bone", "cortisol", "radiation", "mental"];
const STORAGE_KEY = "nasa-space-summary";

interface ArtemisState {
  key: ModuleKey | "ok";
  spriteBase: string;
  title: string;
  bubble: string;
  sarcasm: string;
}

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

function standardBadge(sev: number, lang: string): string {
  const isEn = lang.startsWith("en");
  switch (sev) {
    case 1:
      return "NOMINAL";
    case 2:
      return isEn ? "CAUTION" : "PRECAUCIÓN";
    case 3:
      return isEn ? "WARNING" : "ALERTA";
    case 4:
      return isEn ? "CRITICAL" : "CRÍTICO";
    default:
      return isEn ? "NO DATA" : "SIN DATOS";
  }
}

function ArtemisFloatingSprite({
  spriteBase,
  alt,
}: {
  spriteBase: string;
  alt: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setFailed(false);

    const candidates = [
      `/sprites/${spriteBase}.png`,
      `/sprites/${spriteBase}.jpg`,
      `/${spriteBase}.png`,
      `/${spriteBase}.jpg`,
    ];

    const tryLoad = (index: number) => {
      if (cancelled) return;
      if (index >= candidates.length) {
        setFailed(true);
        return;
      }

      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        if (cancelled) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0);

        const imgData = ctx.getImageData(0, 0, w, h);
        const data = imgData.data;
        const visited = new Uint8Array(w * h);
        const queue = new Int32Array(w * h);
        let head = 0;
        let tail = 0;

        const isOuterDark = (idx: number) => {
          const p = idx * 4;
          return (
            data[p + 3] > 0 &&
            data[p] < 42 &&
            data[p + 1] < 42 &&
            data[p + 2] < 42
          );
        };

        const push = (x: number, y: number) => {
          if (x < 0 || x >= w || y < 0 || y >= h) return;
          const idx = y * w + x;
          if (visited[idx]) return;
          if (isOuterDark(idx)) {
            visited[idx] = 1;
            queue[tail++] = idx;
          }
        };

        for (let x = 0; x < w; x++) {
          push(x, 0);
          push(x, h - 1);
        }
        for (let y = 0; y < h; y++) {
          push(0, y);
          push(w - 1, y);
        }

        while (head < tail) {
          const idx = queue[head++];
          data[idx * 4 + 3] = 0;
          const x = idx % w;
          const y = (idx - x) / w;
          push(x + 1, y);
          push(x - 1, y);
          push(x, y + 1);
          push(x, y - 1);
        }

        ctx.putImageData(imgData, 0, 0);
      };
      img.onerror = () => tryLoad(index + 1);
      img.src = candidates[index];
    };

    tryLoad(0);
    return () => {
      cancelled = true;
    };
  }, [spriteBase]);

  if (failed) {
    return (
      <div className="sprite-missing">
        Coloca <b>{spriteBase}.png</b> en <code>frontend/public/sprites/</code>
      </div>
    );
  }

  return (
    <canvas
      key={spriteBase}
      ref={canvasRef}
      className="artemis-floating-canvas artemis-pop-anim"
      aria-label={alt}
    />
  );
}

export function OverviewView({ astronaut, lang, onOpen }: Props) {
  const { t } = useTranslation();
  const { bone, cortisol, radiation, mental } = useOverview(astronaut, lang);
  const [selected, setSelected] = useState<ModuleKey[]>(readSelection);
  const [activeIndex, setActiveIndex] = useState<number>(0);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
  }, [selected]);

  function toggle(key: ModuleKey) {
    setSelected((current) => {
      if (current.includes(key)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== key);
      }
      return MODULES.filter((item) => current.includes(item) || item === key);
    });
  }

  const boneData = bone.data;
  const cortisolData = cortisol.data;
  const radiationData = radiation.data;
  const mentalData = mental.data;

  const bSev = boneSeverity(boneData?.current?.level);
  const cSev = cortisolSeverity(cortisolData?.current?.color);
  const rSev = radiationSeverity(radiationData?.color);
  const mSev = Math.min(4, mentalData?.global_color ?? 0) as 0 | 1 | 2 | 3 | 4;

  const severities = [bSev, cSev, rSev, mSev];
  const worstSeverity = worst(severities);
  const attention = attentionCount(severities);
  const profile = boneData?.astronaut ?? mentalData?.astronaut ?? null;

  const activeAlerts = useMemo<ArtemisState[]>(() => {
    const list: ArtemisState[] = [];
    if (bSev >= 2) {
      list.push({
        key: "bone",
        spriteBase: "spt_hd",
        title: "ARTEMIS · ALERTA OSTEOMUSCULAR",
        bubble:
          "¡Huesos dañados! Detecto desmineralización acelerada. Tócame para abrir el módulo de Densidad Ósea.",
        sarcasm:
          "Al ritmo que pierde calcio este astronauta, al volver a la Tierra va a crujir como bolsa de papitas. Máxima prioridad al ejercicio en máquina ARED.",
      });
    }
    if (cSev >= 2) {
      list.push({
        key: "cortisol",
        spriteBase: "spt_me",
        title: "ARTEMIS · ALERTA DE CORTISOL",
        bubble:
          "¡Mucho estrés a bordo :c! El pico de cortisol nocturno está saboteando el ritmo circadiano.",
        sarcasm:
          "Ese nivel de cortisol nocturno dice que duerme menos que interno de medicina en guardia de domingo. Prohibido el café liofilizado.",
      });
    }
    if (rSev >= 2) {
      list.push({
        key: "radiation",
        spriteBase: "spt_mr",
        title: "ARTEMIS · ALERTA DOSIMÉTRICA",
        bubble:
          "¡Mucha radiación espacial! La tasa equivalente subió; revisa el blindaje y el acumulado.",
        sarcasm:
          "Dos tormentas solares más a esta dosis y el astronauta no va a necesitar linterna para leer de noche en la cúpula de la ISS.",
      });
    }
    if (mSev >= 2) {
      list.push({
        key: "mental",
        spriteBase: "spt_nt",
        title: "ARTEMIS · SOPORTE PSICOLÓGICO",
        bubble:
          "No estés triste :c. La carga alostática acumulada exige bajar el ritmo operativo de hoy.",
        sarcasm:
          "Ánimo por el piso y sobrecarga cognitiva: si le dan otra ración de comida espacial sin sal, va a pedir traslado a Neptuno.",
      });
    }
    if (list.length === 0) {
      list.push({
        key: "ok",
        spriteBase: "spt_bt",
        title: "ARTEMIS · ESTADO NOMINAL",
        bubble:
          "¡Buen trabajo! Todos los biomarcadores del astronauta están en rango seguro.",
        sarcasm:
          "Signos vitales sospechosamente perfectos. O este astronauta es un cyborg, o desconectó los sensores para dormir hasta tarde.",
      });
    }
    return list;
  }, [bSev, cSev, rSev, mSev]);

  useEffect(() => {
    setActiveIndex(0);
  }, [astronaut, activeAlerts.length]);

  useEffect(() => {
    if (activeAlerts.length <= 1) return;
    const timer = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % activeAlerts.length);
    }, 4500);
    return () => window.clearInterval(timer);
  }, [activeAlerts.length]);

  const currentArtemis = activeAlerts[activeIndex % activeAlerts.length];

  return (
    <div className="labquip-layout">
      <section className="labquip-hero">
        <div className="labquip-hero-left">
          <div className="labquip-kicker">
            <span className="kicker-pulse-dot" />
            <span>TELEMETRÍA BIOASTRONÁUTICA</span>
          </div>

          <h1 className="labquip-giant-title">
            <span className="solid-line">ASTRO HEALTH</span>
            <span className="outline-line">MONITOR APP</span>
          </h1>

          <div className="bio-hud-stream">
            <div className="bio-hud-meta">
              <div className="bio-hud-subject-line">
                <span>
                  SUJETO <b>{profile?.code ?? astronaut}</b>
                </span>
                {profile?.age !== null && profile?.age !== undefined && (
                  <>
                    <i className="hud-sep">//</i>
                    <span>
                      <b>{t("profile.age", { age: profile.age })}</b>
                    </span>
                  </>
                )}
                {profile?.sex && (
                  <>
                    <i className="hud-sep">//</i>
                    <span>
                      <b>{t(`sex.${profile.sex}`)}</b>
                    </span>
                  </>
                )}
              </div>

              <div className={`hud-alert-count s${worstSeverity}`}>
                <i
                  className="fa-solid fa-triangle-exclamation"
                  aria-hidden="true"
                />{" "}
                {attention > 0
                  ? t("overview.attention", { count: attention })
                  : t("overview.nominal")}
              </div>
            </div>

            <div className="bio-hud-counters">
              <div>
                <small>PÉRDIDA ÓSEA</small>
                <strong>
                  {boneData?.current
                    ? `${fmt(boneData.current.cumulative_loss_pct, lang, 1)}%`
                    : "—"}
                </strong>
                <span>
                  {boneData?.current
                    ? `${fmt(boneData.current.rate_pct_month, lang, 2)} %/mes`
                    : ""}
                </span>
              </div>
              <div>
                <small>CORTISOL</small>
                <strong>
                  {cortisolData?.current
                    ? `${fmt(cortisolData.current.value_ug_dl, lang, 2)}`
                    : "—"}
                </strong>
                <span>µg/dL</span>
              </div>
              <div>
                <small>RADIACIÓN</small>
                <strong>
                  {radiationData?.current
                    ? `${fmt(radiationData.current.eq_rate_usv_min, lang, 2)}`
                    : "—"}
                </strong>
                <span>µSv/min</span>
              </div>
              <div>
                <small>CARGA MENTAL</small>
                <strong>
                  {mentalData?.current_tlx
                    ? `TLX ${fmt(mentalData.current_tlx.tlx, lang, 1)}`
                    : "—"}
                </strong>
                <span>pts</span>
              </div>
            </div>

            <p key={currentArtemis.key} className="bio-hud-sarcasm">
              <span>NOTA CLÍNICA DE ARTEMIS:</span> “{currentArtemis.sarcasm}”
            </p>
          </div>

          <div className="labquip-cta-row">
            <button
              type="button"
              className="labquip-btn-primary"
              onClick={() =>
                onOpen(
                  currentArtemis.key === "ok" ? "bone" : currentArtemis.key
                )
              }
            >
              Inspeccionar módulo activo <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>

        <div className="labquip-hero-right">
          <div
            className="artemis-floating-stage"
            onClick={() =>
              onOpen(currentArtemis.key === "ok" ? "bone" : currentArtemis.key)
            }
            role="button"
            tabIndex={0}
            title="Haz clic en Artemis para abrir el módulo en alerta"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onOpen(
                  currentArtemis.key === "ok" ? "bone" : currentArtemis.key
                );
              }
            }}
          >
            <ArtemisFloatingSprite
              spriteBase={currentArtemis.spriteBase}
              alt={currentArtemis.title}
            />
          </div>

          {activeAlerts.length > 1 && (
            <div
              className="artemis-orbit-dots"
              role="tablist"
              aria-label="Alertas activas de Artemis"
            >
              {activeAlerts.map((item, idx) => (
                <button
                  key={item.key}
                  type="button"
                  className={
                    idx === activeIndex % activeAlerts.length ? "on" : ""
                  }
                  onClick={() => setActiveIndex(idx)}
                  title={item.title}
                />
              ))}
            </div>
          )}

          <div className="labquip-mascot-bar">
            <div key={currentArtemis.key} className="labquip-speech-bubble">
              <strong>
                {currentArtemis.title}
                {activeAlerts.length > 1
                  ? ` · ${(activeIndex % activeAlerts.length) + 1}/${activeAlerts.length}`
                  : ""}
              </strong>
              {currentArtemis.bubble}
            </div>
          </div>
        </div>
      </section>

      {/* LEYENDA DISCRETA EN BLANCO DE LA IMAGEN CON HIPERVÍNCULO */}
      <div className="labquip-photo-credit">
        <a
          href="https://www.friendsofnasa.org/search?updated-max=2024-07-31T12:43:00-07:00&max-results=16&reverse-paginate=true&m=0&hl=es-ES"
          target="_blank"
          rel="noopener noreferrer"
        >
          In Darkness viewing Jakarta | International Space Station
        </a>
      </div>

      <div className="labquip-strip-header">
        <div className="labquip-strip-title">
          <span>TELEMETRÍA MULTIPARAMÉTRICA · 4 NODOS ACTIVOS</span>
        </div>

        <div
          className="overview-chips"
          role="group"
          aria-label={t("overview.filter")}
        >
          <button
            type="button"
            className={selected.length === MODULES.length ? "on" : ""}
            onClick={() => setSelected(MODULES)}
          >
            {t("overview.all")}
          </button>
          {MODULES.map((key) => {
            const isSoloOrFiltered =
              selected.length < MODULES.length && selected.includes(key);
            return (
              <button
                key={key}
                type="button"
                className={isSoloOrFiltered ? "on" : ""}
                aria-pressed={selected.includes(key)}
                onClick={() => toggle(key)}
              >
                {t(`view.${key}`)}
              </button>
            );
          })}
        </div>
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
              severity={bSev}
              badge={standardBadge(bSev, lang)}
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
              severity={cSev}
              badge={standardBadge(cSev, lang)}
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
              severity={rSev}
              badge={standardBadge(rSev, lang)}
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
                    ? t(
                        `radiation.layer.status.${radiationData.layers.a.status}`
                      )
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
              spark={radiationData?.readings.map(
                (reading) => reading.eq_rate_usv_min
              )}
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
              severity={mSev}
              badge={standardBadge(mSev, lang)}
              primary={
                mentalData?.current_tlx
                  ? fmt(mentalData.current_tlx.tlx, lang, 1)
                  : "—"
              }
              unit="TLX"
              metrics={[
                {
                  label: t("overview.metric.iad"),
                  value: mentalData?.current_cda
                    ? fmt(mentalData.current_cda.iad, lang, 1)
                    : "—",
                },
                {
                  label: t("overview.metric.tst"),
                  value: mentalData?.current_sleep
                    ? `${fmt(mentalData.current_sleep.tst_min / 60, lang, 1)} h`
                    : "—",
                },
                {
                  label: t("overview.metric.pvt"),
                  value: mentalData?.current_pvt
                    ? fmt(mentalData.current_pvt.speed, lang, 2)
                    : "—",
                },
                {
                  label: t("overview.metric.prescriptions"),
                  value: String(mentalData?.prescriptions.length ?? 0),
                },
              ]}
              updated={
                mentalData?.current_tlx
                  ? formatDateTime(mentalData.current_tlx.taken_at, lang)
                  : null
              }
              spark={mentalData?.tlx_points.map((point) => point.tlx)}
              onOpen={() => onOpen("mental")}
              loading={mental.isLoading}
              error={mental.isError}
              empty={!mentalData?.current_tlx}
            />
          )}
        </div>
      )}

      <footer className="labquip-bottom-credits">
        <p className="labquip-initiative">iniciativa traída por: labquip</p>
        <p className="nasa-challenge-sub">NASA Space Apps Challenge</p>
      </footer>
    </div>
  );
}