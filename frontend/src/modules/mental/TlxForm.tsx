import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, api } from "../../lib/api";
import { fmt } from "../../lib/format";
import type { TlxComparison, TlxSession } from "../../lib/types";

const DIMENSIONS = ["MD", "PD", "TD", "OP", "EF", "FR"] as const;
const PAIRS: Array<[string, string]> = [
  ["MD", "PD"], ["MD", "TD"], ["MD", "OP"], ["MD", "EF"], ["MD", "FR"],
  ["PD", "TD"], ["PD", "OP"], ["PD", "EF"], ["PD", "FR"],
  ["TD", "OP"], ["TD", "EF"], ["TD", "FR"],
  ["OP", "EF"], ["OP", "FR"], ["EF", "FR"],
];
const CATEGORIES = ["eva", "robotics", "maintenance", "science", "flight_ops", "exercise", "simulation", "other"];

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index--) {
    const target = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[target]] = [copy[target], copy[index]];
  }
  return copy;
}

interface Props {
  astronaut: string;
  lang: string;
  onSaved: () => void;
  onToast: (message: string) => void;
}

export function TlxForm({ astronaut, lang, onSaved, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(1);
  const [nonce, setNonce] = useState(0);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("eva");
  const [duration, setDuration] = useState("");
  const [ratings, setRatings] = useState<Record<string, string>>({});
  const [pairIndex, setPairIndex] = useState(0);
  const [choices, setChoices] = useState<TlxComparison[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TlxSession | null>(null);

  const pairs = useMemo(() => shuffle(PAIRS), [nonce]);

  const mutation = useMutation({
    mutationFn: (comparisons: TlxComparison[]) =>
      api.createTlx(
        astronaut,
        {
          task_description: description.trim(),
          task_category: category,
          duration_min: duration ? Number(duration) : null,
          ratings: Object.fromEntries(
            DIMENSIONS.map((dimension) => [dimension, Number(ratings[dimension])]),
          ),
          comparisons,
        },
        lang,
      ),
    onSuccess: (session) => {
      setResult(session);
      setStep(4);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["mental"] });
      onSaved();
      onToast(t("mental.tlx.saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("mental.tlx.error"));
    },
  });

  function reset() {
    setStep(1);
    setNonce((value) => value + 1);
    setDescription("");
    setCategory("eva");
    setDuration("");
    setRatings({});
    setPairIndex(0);
    setChoices([]);
    setResult(null);
    setError(null);
  }

  function startRatings() {
    if (description.trim().length < 3) {
      setError(t("mental.tlx.error_description"));
      return;
    }
    setError(null);
    setStep(2);
  }

  function startPairs() {
    const missing = DIMENSIONS.some((dimension) => ratings[dimension] === undefined);
    if (missing) {
      setError(t("mental.tlx.error_ratings"));
      return;
    }
    setError(null);
    setStep(3);
  }

  function choose(dimension: string) {
    const pair = pairs[pairIndex];
    const next = [...choices, { pair: [...pair], choice: dimension }];
    setChoices(next);
    if (pairIndex + 1 >= pairs.length) {
      mutation.mutate(next);
    } else {
      setPairIndex(pairIndex + 1);
    }
  }

  return (
    <section className="panel questionnaire-card">
      <h2>{t("mental.tlx.title")}</h2>
      <p className="hint">{t("mental.tlx.hint")}</p>

      {step === 1 && (
        <>
          <div className="field">
            <label htmlFor="tlx-task">{t("mental.tlx.task")}</label>
            <input
              id="tlx-task"
              type="text"
              maxLength={300}
              value={description}
              placeholder={t("mental.tlx.task_placeholder")}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          <div className="row2">
            <div className="field">
              <label htmlFor="tlx-category">{t("mental.tlx.category")}</label>
              <select
                id="tlx-category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                {CATEGORIES.map((key) => (
                  <option key={key} value={key}>
                    {t(`mental.category.${key}`)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="tlx-duration">{t("mental.tlx.duration")}</label>
              <input
                id="tlx-duration"
                type="number"
                min="1"
                max="1440"
                value={duration}
                onChange={(event) => setDuration(event.target.value)}
              />
            </div>
          </div>
          <div className="actions">
            <button type="button" className="primary" onClick={startRatings}>
              {t("mental.tlx.continue")}
            </button>
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <h3 className="form-section">{t("mental.tlx.ratings_title")}</h3>
          <p className="hint">{t("mental.tlx.ratings_hint")}</p>
          <div className="scale-grid">
            {DIMENSIONS.map((dimension) => (
              <label key={dimension} className="scale-row">
                <span>{t(`mental.dimension.${dimension}`)}</span>
                <select
                  value={ratings[dimension] ?? ""}
                  onChange={(event) =>
                    setRatings({ ...ratings, [dimension]: event.target.value })
                  }
                >
                  <option value="">—</option>
                  {Array.from({ length: 21 }, (_, index) => index * 5).map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <div className="actions">
            <button type="button" onClick={() => setStep(1)}>
              {t("mental.tlx.back")}
            </button>
            <button type="button" className="primary" onClick={startPairs}>
              {t("mental.tlx.continue")}
            </button>
          </div>
        </>
      )}

      {step === 3 && (
        <>
          <h3 className="form-section">
            {t("mental.tlx.pairs_title", { current: pairIndex + 1, total: pairs.length })}
          </h3>
          <p className="hint">{t("mental.tlx.pairs_hint")}</p>
          <div className="pair-grid">
            {pairs[pairIndex].map((dimension) => (
              <button
                key={dimension}
                type="button"
                className="pair-button"
                disabled={mutation.isPending}
                onClick={() => choose(dimension)}
              >
                {t(`mental.dimension.${dimension}`)}
              </button>
            ))}
          </div>
          <div className="actions">
            {pairIndex > 0 && (
              <button
                type="button"
                onClick={() => {
                  setPairIndex(pairIndex - 1);
                  setChoices(choices.slice(0, -1));
                }}
                disabled={mutation.isPending}
              >
                {t("mental.tlx.back")}
              </button>
            )}
          </div>
        </>
      )}

      {step === 4 && result && (
        <>
          <div className="tlx-result">
            <div>
              <span className="label">NASA-TLX</span>
              <b>{fmt(result.tlx, lang, 2)}</b>
            </div>
            <div>
              <span className="label">RTLX</span>
              <b>{fmt(result.rtlx, lang, 2)}</b>
            </div>
            <div>
              <span className="label">{t("mental.tlx.dominant")}</span>
              <b>{t(`mental.dimension.${result.dominant}`)}</b>
            </div>
          </div>
          <div className="tbl">
            <table>
              <thead>
                <tr>
                  <th>{t("mental.tlx.dimension")}</th>
                  <th>{t("mental.tlx.rating")}</th>
                  <th>{t("mental.tlx.count")}</th>
                  <th>{t("mental.tlx.weight")}</th>
                  <th>{t("mental.tlx.contribution")}</th>
                </tr>
              </thead>
              <tbody>
                {DIMENSIONS.map((dimension) => (
                  <tr key={dimension}>
                    <td>{t(`mental.dimension.${dimension}`)}</td>
                    <td>{result.ratings[dimension]}</td>
                    <td>{result.counts[dimension]}</td>
                    <td>{fmt(result.weights[dimension], lang, 3)}</td>
                    <td>{fmt(result.contributions[dimension], lang, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="actions">
            <button type="button" className="primary" onClick={reset}>
              {t("mental.tlx.new")}
            </button>
          </div>
        </>
      )}

      <p className="err" role="alert">
        {error ?? ""}
      </p>
    </section>
  );
}
