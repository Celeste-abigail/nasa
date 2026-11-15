import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, api } from "../../lib/api";
import { fmt, todayISO } from "../../lib/format";
import type { CdaPoint } from "../../lib/types";
import { TemporalField } from "../../components/TemporalField";

const ITEMS = [
  ["animo", "+"],
  ["energia", "+"],
  ["motivacion", "+"],
  ["tension", "-"],
  ["tristeza", "-"],
  ["irritabilidad", "-"],
  ["estres", "-"],
  ["fatiga_mental", "-"],
  ["sueno", "+"],
  ["conexion", "+"],
] as const;

interface Props {
  astronaut: string;
  lang: string;
  onSaved: () => void;
  onToast: (message: string) => void;
}

export function CdaForm({ astronaut, lang, onSaved, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [day, setDay] = useState(todayISO());
  const [values, setValues] = useState<Record<string, number>>(
    Object.fromEntries(ITEMS.map(([key]) => [key, 5])),
  );
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CdaPoint | null>(null);

  const mutation = useMutation({
    mutationFn: () => api.saveCda(astronaut, day, values, lang),
    onSuccess: (point) => {
      setResult(point);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["mental"] });
      onSaved();
      onToast(t("mental.cda.saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("mental.cda.error"));
    },
  });

  return (
    <section className="panel questionnaire-card">
      <h2>{t("mental.cda.title")}</h2>
      <p className="hint">{t("mental.cda.hint")}</p>

      <TemporalField
        id="cda-day"
        label={t("mental.cda.day")}
        mode="date"
        value={day}
        max={todayISO()}
        onChange={setDay}
      />

      <div className="mood-grid">
        {ITEMS.map(([key, direction]) => (
          <label key={key}>
            <span>
              {t(`mental.cda.item.${key}`)}{" "}
              <small className="optional">{direction === "+" ? "+" : "−"}</small>
            </span>
            <input
              type="range"
              min="0"
              max="10"
              step="1"
              value={values[key]}
              onChange={(event) =>
                setValues({ ...values, [key]: Number(event.target.value) })
              }
            />
            <b>{values[key]}</b>
          </label>
        ))}
      </div>

      <p className="err" role="alert">
        {error ?? ""}
      </p>

      <div className="actions">
        <button
          type="button"
          className="primary"
          disabled={mutation.isPending}
          onClick={() => {
            setError(null);
            mutation.mutate();
          }}
        >
          {mutation.isPending ? t("mental.cda.saving") : t("mental.cda.submit")}
        </button>
      </div>

      {result && (
        <div className="cortisol-cards" style={{ marginTop: 14 }}>
          <div className="cortisol-card">
            <h3>{t("mental.cda.iad")}</h3>
            <b>{fmt(result.iad, lang, 1)}</b>
            <span>{t(`mental.status.${result.color}`)}</span>
          </div>
          <div className="cortisol-card">
            <h3>{t("mental.cda.positive")}</h3>
            <b>{fmt(result.positive, lang, 1)}</b>
            <span>
              {t("mental.cda.negative")}: {fmt(result.negative, lang, 1)}
            </span>
          </div>
          <div className="cortisol-card">
            <h3>{t("mental.cda.stress")}</h3>
            <b>{fmt(result.stress_fatigue, lang, 1)}</b>
            <span>
              {t("mental.cda.sleep")}: {fmt(result.sleep, lang, 1)} ·{" "}
              {t("mental.cda.connection")}: {fmt(result.connection, lang, 1)}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
