import { useId } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  bone: number;
  radiation: number;
  stress: number;
}

const CYAN = "#38bdf8";
const AMBER = "#fbbf24";
const RED = "#fb7185";

function layerColor(severity: number): string {
  if (severity >= 3) return RED;
  if (severity >= 2) return AMBER;
  return CYAN;
}

export function BodyDiagnostic({ bone, radiation, stress }: Props) {
  const { t } = useTranslation();
  const uid = useId().replace(/[:]/g, "");
  const worst = Math.max(bone, radiation, stress);
  const critical = worst >= 3;

  const boneColor = layerColor(bone);
  const stressColor = layerColor(stress);
  const radiationColor = layerColor(radiation);
  const status =
    worst >= 3
      ? t("overview.body.critical")
      : worst >= 2
        ? t("overview.body.watch")
        : t("overview.body.normal");

  const active = [
    bone >= 2 ? t("overview.body.bone") : null,
    radiation >= 2 ? t("overview.body.radiation") : null,
    stress >= 2 ? t("overview.body.stress") : null,
  ].filter(Boolean);

  return (
    <figure
      className={`body-diagnostic s${worst}${critical ? " is-critical" : ""}`}
      aria-label={t("overview.body.aria", {
        status,
        systems: active.length ? active.join(", ") : t("overview.body.none"),
      })}
    >
      <svg viewBox="0 0 200 380" role="img" aria-hidden="true">
        <defs>
          <radialGradient id={`halo-${uid}`} cx="50%" cy="45%" r="60%">
            <stop offset="0%" stopColor={CYAN} stopOpacity="0.18" />
            <stop offset="100%" stopColor={CYAN} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`head-${uid}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={stressColor} stopOpacity={stress >= 2 ? 0.95 : 0.35} />
            <stop offset="100%" stopColor={stressColor} stopOpacity="0" />
          </radialGradient>
          <filter id={`glow-${uid}`} x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="2.6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id={`aura-${uid}`} x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="12" />
          </filter>
        </defs>

        <ellipse cx="100" cy="190" rx="92" ry="182" fill={`url(#halo-${uid})`} />

        {radiation >= 2 && (
          <g filter={`url(#aura-${uid})`} opacity={radiation >= 3 ? 0.4 : 0.26} className="body-aura">
            <circle cx="100" cy="40" r="22" fill="none" stroke={radiationColor} strokeWidth="16" />
            <path
              d="M62 78 L40 210 M138 78 L160 210 M80 214 L78 350 M120 214 L122 350"
              stroke={radiationColor}
              strokeWidth="18"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M62 74 Q100 60 138 74 L132 196 Q100 214 68 196 Z"
              fill="none"
              stroke={radiationColor}
              strokeWidth="18"
            />
          </g>
        )}

        {/* Silueta holográfica */}
        <g
          fill="none"
          stroke={CYAN}
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.5"
        >
          <circle cx="100" cy="40" r="21" />
          <path d="M62 78 L40 208 M138 78 L160 208" />
          <path d="M80 214 L77 350 M120 214 L123 350" />
          <path d="M62 74 Q100 58 138 74 L132 198 Q100 212 68 198 Z" fill="rgba(56,189,248,0.06)" />
        </g>

        {/* Esqueleto */}
        <g
          stroke={boneColor}
          strokeWidth="1.7"
          strokeLinecap="round"
          fill="none"
          filter={`url(#glow-${uid})`}
          className="body-skeleton"
        >
          <ellipse cx="100" cy="38" rx="13" ry="16" />
          <path d="M90 47 L90 51 M110 47 L110 51 M95 47 L95 50 M105 47 L105 50" />
          <path d="M100 55 L100 192" />
          {[0, 1, 2, 3, 4].map((index) => (
            <g key={`rib-${index}`}>
              <path d={`M100 ${72 + index * 12} Q76 ${76 + index * 12} 74 ${86 + index * 12}`} />
              <path d={`M100 ${72 + index * 12} Q124 ${76 + index * 12} 126 ${86 + index * 12}`} />
            </g>
          ))}
          <path d="M100 66 L72 80 M100 66 L128 80" />
          <path d="M72 78 L52 130 L48 176 M128 78 L148 130 L152 176" />
          <path d="M48 176 L44 200 M152 176 L156 200" />
          <path d="M78 196 Q100 186 122 196 L118 210 Q100 218 82 210 Z" />
          <path d="M84 210 L73 268 L77 344 M116 210 L127 268 L123 344" />
          <path d="M77 344 L70 356 M123 344 L130 356" />
        </g>

        {/* Cabeza / estrés */}
        <circle
          cx="100"
          cy="38"
          r={stress >= 2 ? 24 : 18}
          fill={`url(#head-${uid})`}
          className="body-head"
        />

        {/* Líneas de escaneo */}
        <g stroke="#7dd3fc" strokeWidth="0.5" opacity="0.1">
          {Array.from({ length: 18 }, (_, index) => (
            <line key={index} x1="14" x2="186" y1={20 + index * 20} y2={20 + index * 20} />
          ))}
        </g>
      </svg>

      <figcaption>
        <div className={`body-status s${worst}`}>{status}</div>
        <ul className="body-legend">
          <li className={bone >= 2 ? `s${bone}` : ""}>
            <i />
            {t("overview.body.bone")}
          </li>
          <li className={radiation >= 2 ? `s${radiation}` : ""}>
            <i />
            {t("overview.body.radiation")}
          </li>
          <li className={stress >= 2 ? `s${stress}` : ""}>
            <i />
            {t("overview.body.stress")}
          </li>
        </ul>
      </figcaption>
    </figure>
  );
}
