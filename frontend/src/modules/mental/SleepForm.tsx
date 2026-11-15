import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, api } from "../../lib/api";
import { addDays, fmt, todayISO } from "../../lib/format";
import type { CauseGroup, Dreams, SleepNight, SleepProfile } from "../../lib/types";
import { TemporalField } from "../../components/TemporalField";

const LATENCIES = [5, 10, 15, 20, 30, 45, 60, 90];
const CAUSES_A = ["pending", "repetitive", "anxiety"];
const CAUSES_B = ["noise", "temperature", "light", "alarm", "sack", "physiological", "other"];
const ENVIRONMENTAL = ["headache", "air", "noise", "nothing"];
const DREAMS: Dreams[] = ["none", "neutral", "vivid", "nightmare"];

interface Props {
  astronaut: string;
  lang: string;
  profile: SleepProfile;
  onSaved: () => void;
  onToast: (message: string) => void;
}

export function SleepForm({ astronaut, lang, profile, onSaved, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [needHours, setNeedHours] = useState(String(profile.need_hours));
  const [scheduledWake, setScheduledWake] = useState(profile.scheduled_wake);
  const [windowMinutes, setWindowMinutes] = useState(String(profile.window_minutes));
  const [blocked, setBlocked] = useState(profile.blocked);

  const [day, setDay] = useState(todayISO());
  const [entryAt, setEntryAt] = useState(`${addDays(todayISO(), -1)}T22:30`);
  const [finalWake, setFinalWake] = useState(`${todayISO()}T05:50`);
  const [exitAt, setExitAt] = useState(`${todayISO()}T06:10`);
  const [latency, setLatency] = useState(25);
  const [awakenings, setAwakenings] = useState(0);
  const [waso, setWaso] = useState(0);
  const [causeGroup, setCauseGroup] = useState<CauseGroup | "">("");
  const [causeDetail, setCauseDetail] = useState("");
  const [quality, setQuality] = useState(6);
  const [inertia, setInertia] = useState(3);
  const [dreams, setDreams] = useState<Dreams>("neutral");
  const [environmental, setEnvironmental] = useState<string[]>(["nothing"]);
  const [nap, setNap] = useState("0");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SleepNight | null>(null);

  const profileMutation = useMutation({
    mutationFn: () =>
      api.saveSleepProfile(
        astronaut,
        {
          need_hours: Number(needHours),
          scheduled_wake: scheduledWake,
          window_minutes: Number(windowMinutes),
          blocked,
          last_adjustment: profile.last_adjustment,
        },
        lang,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mental"] });
      onToast(t("mental.sleep.profile_saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("mental.sleep.error"));
    },
  });

  const nightMutation = useMutation({
    mutationFn: () =>
      api.saveSleepNight(
        astronaut,
        day,
        {
          day,
          entry_at: entryAt.length === 16 ? `${entryAt}:00` : entryAt,
          latency_min: latency,
          awakenings,
          waso_min: awakenings > 0 ? waso : 0,
          cause_group: causeGroup || null,
          cause_detail: causeDetail || null,
          final_wake_at: finalWake.length === 16 ? `${finalWake}:00` : finalWake,
          exit_at: exitAt.length === 16 ? `${exitAt}:00` : exitAt,
          quality,
          inertia,
          dreams,
          environmental,
          nap_min: nap ? Number(nap) : null,
        },
        lang,
      ),
    onSuccess: (night) => {
      setResult(night);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["mental"] });
      onSaved();
      onToast(t("mental.sleep.saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("mental.sleep.error"));
    },
  });

  function toggleEnvironmental(value: string) {
    setEnvironmental((current) => {
      if (value === "nothing") return ["nothing"];
      const next = current.filter((item) => item !== "nothing");
      return next.includes(value)
        ? next.filter((item) => item !== value)
        : [...next, value];
    });
  }

  return (
    <section className="panel questionnaire-card">
      <h2>{t("mental.sleep.title")}</h2>
      <p className="hint">{t("mental.sleep.hint")}</p>

      <h3 className="form-section">{t("mental.sleep.profile_title")}</h3>
      <div className="row2">
        <div className="field">
          <label htmlFor="sleep-need">{t("mental.sleep.need_hours")}</label>
          <input
            id="sleep-need"
            type="number"
            min="4"
            max="12"
            step="0.5"
            value={needHours}
            onChange={(event) => setNeedHours(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="sleep-wake">{t("mental.sleep.scheduled_wake")}</label>
          <input
            id="sleep-wake"
            type="time"
            value={scheduledWake}
            onChange={(event) => setScheduledWake(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="sleep-window">{t("mental.sleep.window")}</label>
          <input
            id="sleep-window"
            type="number"
            min="240"
            max="720"
            step="15"
            value={windowMinutes}
            onChange={(event) => setWindowMinutes(event.target.value)}
          />
        </div>
        <label className="check-row">
          <input
            type="checkbox"
            checked={blocked}
            onChange={(event) => setBlocked(event.target.checked)}
          />
          <span>{t("mental.sleep.blocked")}</span>
        </label>
      </div>
      <div className="actions">
        <button type="button" onClick={() => profileMutation.mutate()}>
          {t("mental.sleep.save_profile")}
        </button>
      </div>

      <h3 className="form-section">{t("mental.sleep.night_title")}</h3>
      <div className="row2">
        <TemporalField
          id="sleep-day"
          label={t("mental.sleep.day")}
          mode="date"
          value={day}
          max={todayISO()}
          onChange={setDay}
        />
        <div className="field">
          <label htmlFor="sleep-latency">{t("mental.sleep.latency")}</label>
          <select
            id="sleep-latency"
            value={latency}
            onChange={(event) => setLatency(Number(event.target.value))}
          >
            {LATENCIES.map((value) => (
              <option key={value} value={value}>
                {value} min
              </option>
            ))}
          </select>
        </div>
      </div>

      <TemporalField
        id="sleep-entry"
        label={t("mental.sleep.entry")}
        value={entryAt}
        utc
        onChange={setEntryAt}
      />
      <div className="row2">
        <TemporalField
          id="sleep-final"
          label={t("mental.sleep.final_wake")}
          value={finalWake}
          utc
          onChange={setFinalWake}
        />
        <TemporalField
          id="sleep-exit"
          label={t("mental.sleep.exit")}
          value={exitAt}
          utc
          onChange={setExitAt}
        />
      </div>

      <div className="row2">
        <div className="field">
          <label htmlFor="sleep-awakenings">{t("mental.sleep.awakenings")}</label>
          <input
            id="sleep-awakenings"
            type="number"
            min="0"
            max="20"
            value={awakenings}
            onChange={(event) => setAwakenings(Number(event.target.value))}
          />
        </div>
        <div className="field">
          <label htmlFor="sleep-waso">{t("mental.sleep.waso")}</label>
          <input
            id="sleep-waso"
            type="number"
            min="0"
            max="600"
            step="5"
            value={waso}
            disabled={awakenings === 0}
            onChange={(event) => setWaso(Number(event.target.value))}
          />
        </div>
      </div>

      <div className="row2">
        <div className="field">
          <label htmlFor="sleep-cause">{t("mental.sleep.cause")}</label>
          <select
            id="sleep-cause"
            value={causeGroup}
            onChange={(event) => {
              setCauseGroup(event.target.value as CauseGroup | "");
              setCauseDetail("");
            }}
          >
            <option value="">—</option>
            <option value="A">{t("mental.sleep.cause_a")}</option>
            <option value="B">{t("mental.sleep.cause_b")}</option>
          </select>
        </div>
        {causeGroup && (
          <div className="field">
            <label htmlFor="sleep-detail">{t("mental.sleep.cause_detail")}</label>
            <select
              id="sleep-detail"
              value={causeDetail}
              onChange={(event) => setCauseDetail(event.target.value)}
            >
              <option value="">—</option>
              {(causeGroup === "A" ? CAUSES_A : CAUSES_B).map((key) => (
                <option key={key} value={key}>
                  {t(`mental.sleep.detail.${key}`)}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="row2">
        <label className="scale-row">
          <span>{t("mental.sleep.quality")}</span>
          <input
            type="range"
            min="0"
            max="10"
            value={quality}
            onChange={(event) => setQuality(Number(event.target.value))}
          />
          <b>{quality}</b>
        </label>
        <label className="scale-row">
          <span>{t("mental.sleep.inertia")}</span>
          <input
            type="range"
            min="0"
            max="10"
            value={inertia}
            onChange={(event) => setInertia(Number(event.target.value))}
          />
          <b>{inertia}</b>
        </label>
      </div>

      <div className="row2">
        <div className="field">
          <label htmlFor="sleep-dreams">{t("mental.sleep.dreams")}</label>
          <select
            id="sleep-dreams"
            value={dreams}
            onChange={(event) => setDreams(event.target.value as Dreams)}
          >
            {DREAMS.map((key) => (
              <option key={key} value={key}>
                {t(`mental.sleep.dream.${key}`)}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="sleep-nap">{t("mental.sleep.nap")}</label>
          <input
            id="sleep-nap"
            type="number"
            min="0"
            max="600"
            step="5"
            value={nap}
            onChange={(event) => setNap(event.target.value)}
          />
        </div>
      </div>

      {inertia >= 7 && (
        <div className="field">
          <span className="label">{t("mental.sleep.environmental")}</span>
          <div className="check-grid">
            {ENVIRONMENTAL.map((key) => (
              <label key={key} className="check-row">
                <input
                  type="checkbox"
                  checked={environmental.includes(key)}
                  onChange={() => toggleEnvironmental(key)}
                />
                <span>{t(`mental.sleep.env.${key}`)}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <p className="err" role="alert">
        {error ?? ""}
      </p>

      <div className="actions">
        <button
          type="button"
          className="primary"
          disabled={nightMutation.isPending}
          onClick={() => {
            setError(null);
            nightMutation.mutate();
          }}
        >
          {nightMutation.isPending ? t("mental.sleep.saving") : t("mental.sleep.submit")}
        </button>
      </div>

      {result && (
        <div className="cortisol-cards" style={{ marginTop: 14 }}>
          <div className="cortisol-card">
            <h3>{t("mental.sleep.tst")}</h3>
            <b>{fmt(result.tst_min / 60, lang, 2)} h</b>
            <span>
              {t("mental.sleep.efficiency")}: {fmt(result.efficiency, lang, 1)} %
            </span>
          </div>
          <div className="cortisol-card">
            <h3>{t("mental.sleep.tib")}</h3>
            <b>{fmt(result.tib_min / 60, lang, 2)} h</b>
            <span>{t(`mental.status.${result.color}`)}</span>
          </div>
          <div className="cortisol-card">
            <h3>{t("mental.sleep.debt")}</h3>
            <b>{fmt(result.debt_hours, lang, 2)} h</b>
            <span>
              {t("mental.sleep.se7")}:{" "}
              {result.se7 === null ? "—" : `${fmt(result.se7, lang, 1)} %`}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
