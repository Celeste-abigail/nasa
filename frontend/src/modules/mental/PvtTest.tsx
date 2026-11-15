import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, api } from "../../lib/api";
import { fmt } from "../../lib/format";
import type { PvtTest } from "../../lib/types";

interface Props {
  astronaut: string;
  lang: string;
  onSaved: () => void;
  onToast: (message: string) => void;
}

export function PvtTestPanel({ astronaut, lang, onSaved, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<60 | 180>(60);
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [visible, setVisible] = useState(false);
  const [remaining, setRemaining] = useState(60);
  const [alertness, setAlertness] = useState(5);
  const [result, setResult] = useState<PvtTest | null>(null);
  const [error, setError] = useState<string | null>(null);

  const trials = useRef<number[]>([]);
  const falseStarts = useRef(0);
  const stimulusAt = useRef(0);
  const scheduleTimer = useRef<number | null>(null);
  const tickTimer = useRef<number | null>(null);
  const endAt = useRef(0);
  const finished = useRef(false);

  const mutation = useMutation({
    mutationFn: () =>
      api.createPvt(
        astronaut,
        {
          mode,
          trials: trials.current,
          false_starts: falseStarts.current,
          subjective_alertness: alertness,
        },
        lang,
      ),
    onSuccess: (test) => {
      setResult(test);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["mental"] });
      onSaved();
      onToast(t("mental.pvt.saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("mental.pvt.error"));
    },
  });

  function cleanup() {
    if (scheduleTimer.current !== null) window.clearTimeout(scheduleTimer.current);
    if (tickTimer.current !== null) window.clearInterval(tickTimer.current);
    scheduleTimer.current = null;
    tickTimer.current = null;
  }

  function schedule() {
    setVisible(false);
    scheduleTimer.current = window.setTimeout(() => {
      stimulusAt.current = performance.now();
      setVisible(true);
    }, 1000 + Math.random() * 3000);
  }

  function finish() {
    if (finished.current) return;
    finished.current = true;
    cleanup();
    setVisible(false);
    setPhase("done");
    mutation.mutate();
  }

  function respond() {
    if (phase !== "running" || finished.current) return;
    if (!visible) {
      falseStarts.current += 1;
      return;
    }
    const rt = Math.round(performance.now() - stimulusAt.current);
    trials.current.push(rt);
    setVisible(false);
    if (scheduleTimer.current !== null) window.clearTimeout(scheduleTimer.current);
    if (performance.now() < endAt.current) {
      schedule();
    } else {
      finish();
    }
  }

  function start() {
    cleanup();
    trials.current = [];
    falseStarts.current = 0;
    finished.current = false;
    setResult(null);
    setError(null);
    setPhase("running");
    setRemaining(mode);
    endAt.current = performance.now() + mode * 1000;
    schedule();
    tickTimer.current = window.setInterval(() => {
      const left = Math.max(0, Math.ceil((endAt.current - performance.now()) / 1000));
      setRemaining(left);
      if (left <= 0) finish();
    }, 200);
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.code !== "Space") return;
      if (phase !== "running") return;
      event.preventDefault();
      respond();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  useEffect(() => cleanup, []);

  return (
    <section className="panel questionnaire-card">
      <h2>{t("mental.pvt.title")}</h2>
      <p className="hint">{t("mental.pvt.hint")}</p>

      {phase === "idle" && (
        <>
          <div className="field">
            <label htmlFor="pvt-mode">{t("mental.pvt.mode")}</label>
            <select
              id="pvt-mode"
              value={mode}
              onChange={(event) => setMode(Number(event.target.value) as 60 | 180)}
            >
              <option value={60}>{t("mental.pvt.mode_fast")}</option>
              <option value={180}>{t("mental.pvt.mode_full")}</option>
            </select>
          </div>
          <label className="scale-row">
            <span>{t("mental.pvt.alertness")}</span>
            <input
              type="range"
              min="0"
              max="10"
              value={alertness}
              onChange={(event) => setAlertness(Number(event.target.value))}
            />
            <b>{alertness}</b>
          </label>
          <p className="hint">{t("mental.pvt.instructions")}</p>
          <div className="actions">
            <button type="button" className="primary" onClick={start}>
              {t("mental.pvt.start")}
            </button>
          </div>
        </>
      )}

      {phase === "running" && (
        <div className="pvt-overlay" onMouseDown={respond} role="presentation">
          <div className="pvt-timer">
            {remaining}s · {t("mental.pvt.waiting")}
          </div>
          {visible ? (
            <div className="pvt-stimulus" aria-label={t("mental.pvt.stimulus")} />
          ) : (
            <p className="pvt-idle-text">{t("mental.pvt.wait")}</p>
          )}
          <p className="pvt-help">{t("mental.pvt.respond_hint")}</p>
        </div>
      )}

      {phase === "done" && (
        <>
          {result && (
            <div className="cortisol-cards">
              <div className="cortisol-card">
                <h3>{t("mental.pvt.speed")}</h3>
                <b>{fmt(result.speed, lang, 2)}</b>
                <span>
                  {t("mental.pvt.mean_rt")}: {fmt(result.mean_rt_ms, lang, 1)} ms
                </span>
              </div>
              <div className="cortisol-card">
                <h3>{t("mental.pvt.valid")}</h3>
                <b>{result.valid_count}</b>
                <span>
                  {t("mental.pvt.lapses")}: {result.lapses} ·{" "}
                  {t("mental.pvt.false_starts")}: {result.false_starts}
                </span>
              </div>
              <div className="cortisol-card">
                <h3>{t("mental.pvt.alert")}</h3>
                <b>
                  {result.color ? t(`mental.status.${result.color}`) : t("mental.pvt.calibrating")}
                </b>
                <span>
                  {result.z === null ? "—" : `z ${fmt(result.z, lang, 2)}`}
                  {result.discrepancy ? ` · ${t("mental.pvt.discrepancy")}` : ""}
                </span>
              </div>
            </div>
          )}
          <div className="actions">
            <button type="button" className="primary" onClick={start}>
              {t("mental.pvt.repeat")}
            </button>
            <button type="button" onClick={() => setPhase("idle")}>
              {t("mental.pvt.finish")}
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
