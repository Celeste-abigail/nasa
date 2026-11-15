import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Astronaut } from "../../lib/types";
import { DownloadMenu } from "./DownloadMenu";

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

function LabquipBrandLogo() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const candidates = [
      "/artemis_logo.png",
      "/labquip-logo.png",
      "/sprites/artemis_logo.png",
    ];

    const tryLoad = (idx: number) => {
      if (cancelled) return;
      if (idx >= candidates.length) {
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
        ctx.drawImage(img, 0, 0);

        const imgData = ctx.getImageData(0, 0, w, h);
        const data = imgData.data;
        const visited = new Uint8Array(w * h);
        const queue = new Int32Array(w * h);
        let head = 0;
        let tail = 0;

        // 1. Elimina el fondo blanco exterior alrededor del círculo
        const isOuterLight = (i: number) => {
          const p = i * 4;
          return (
            data[p + 3] > 0 &&
            data[p] > 200 &&
            data[p + 1] > 200 &&
            data[p + 2] > 200
          );
        };

        const push = (x: number, y: number) => {
          if (x < 0 || x >= w || y < 0 || y >= h) return;
          const i = y * w + x;
          if (visited[i]) return;
          if (isOuterLight(i)) {
            visited[i] = 1;
            queue[tail++] = i;
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
          const i = queue[head++];
          data[i * 4 + 3] = 0;
          const x = i % w;
          const y = (i - x) / w;
          push(x + 1, y);
          push(x - 1, y);
          push(x, y + 1);
          push(x, y - 1);
        }

        // 2. Recorta al borde exacto del círculo y aplica la paleta Abisal-Nebulosa
        let minX = w,
          minY = h,
          maxX = 0,
          maxY = 0;
        for (let i = 0; i < w * h; i++) {
          const p = i * 4;
          if (data[p + 3] === 0) continue;
          const x = i % w;
          const y = (i - x) / w;
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;

          const lum = (data[p] + data[p + 1] + data[p + 2]) / (3 * 255);
          const grad = (x + y) / (w + h);

          // Círculo de fondo: Azul abisal (#060d1c)
          const darkR = 6,
            darkG = 13,
            darkB = 28;
          // Líneas de la tortuga y cruz: Degradado Cian (#7dd3fc) a Violeta claro (#c4b5fd)
          const lightR = Math.round(125 * (1 - grad * 0.45) + 196 * (grad * 0.45));
          const lightG = Math.round(211 * (1 - grad * 0.45) + 181 * (grad * 0.45));
          const lightB = 252;

          data[p] = Math.round(darkR + (lightR - darkR) * lum);
          data[p + 1] = Math.round(darkG + (lightG - darkG) * lum);
          data[p + 2] = Math.round(darkB + (lightB - darkB) * lum);
        }

        ctx.putImageData(imgData, 0, 0);

        if (maxX > minX && maxY > minY) {
          const cw = maxX - minX + 1;
          const ch = maxY - minY + 1;
          const cropped = ctx.getImageData(minX, minY, cw, ch);
          canvas.width = cw;
          canvas.height = ch;
          ctx.putImageData(cropped, 0, 0);
        }
      };
      img.onerror = () => tryLoad(idx + 1);
      img.src = candidates[idx];
    };

    tryLoad(0);
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return <i className="fa-solid fa-satellite" aria-hidden="true" />;
  }

  return (
    <canvas
      ref={canvasRef}
      className="labquip-logo-canvas"
      aria-hidden="true"
    />
  );
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
          <a
            href="https://www.spaceappschallenge.org/2026/find-a-team/labquip/"
            target="_blank"
            rel="noopener noreferrer"
            className="labquip-badge-logo"
            title="NASA Space Apps Challenge · Team LABQUIP"
          >
            <LabquipBrandLogo />
            <span>LABQUIP</span>
          </a>

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

          <DownloadMenu astronaut={astronaut} lang={lang} />

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