import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, api } from "../../lib/api";
import { todayISO } from "../../lib/format";
import type { Sex } from "../../lib/types";
import { TemporalField } from "../../components/TemporalField";

interface Props {
  open: boolean;
  onClose: () => void;
  active: string;
  onSelect: (code: string) => void;
  lang: string;
  onToast: (message: string) => void;
}

type Tab = "active" | "archived";

export function CrewManager({ open, onClose, active, onSelect, lang, onToast }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("active");
  const [confirming, setConfirming] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [sex, setSex] = useState<Sex>("male");
  const [birthDate, setBirthDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const activeQuery = useQuery({
    queryKey: ["astronauts", lang],
    queryFn: () => api.astronauts(lang),
    enabled: open,
  });

  const archivedQuery = useQuery({
    queryKey: ["astronauts-archived", lang],
    queryFn: () => api.archivedAstronauts(lang),
    enabled: open,
  });

  function refreshAll() {
    void queryClient.invalidateQueries();
  }

  const createMutation = useMutation({
    mutationFn: () =>
      api.createAstronaut(
        { code: code.trim().toUpperCase(), name: name.trim(), sex, birth_date: birthDate },
        lang,
      ),
    onSuccess: (astronaut) => {
      setError(null);
      setCode("");
      setName("");
      setBirthDate("");
      refreshAll();
      onSelect(astronaut.code);
      onToast(t("crew.saved"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("crew.error"));
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (target: string) => api.archiveAstronaut(target, lang),
    onSuccess: (_data, target) => {
      setConfirming(null);
      refreshAll();
      if (target === active) {
        const next = (activeQuery.data ?? []).find((item) => item.code !== target);
        if (next) onSelect(next.code);
      }
      onToast(t("crew.archived"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("crew.error"));
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (target: string) => api.restoreAstronaut(target, lang),
    onSuccess: () => {
      refreshAll();
      onToast(t("crew.restored"));
    },
    onError: (reason) => {
      setError(reason instanceof ApiError ? reason.message : t("crew.error"));
    },
  });

  if (!open) return null;

  const activeList = activeQuery.data ?? [];
  const archivedList = archivedQuery.data ?? [];
  const busy =
    createMutation.isPending || archiveMutation.isPending || restoreMutation.isPending;

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="crew-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-head">
          <h2 id="crew-title">{t("crew.title")}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label={t("crew.close")}>
            <i className="fa-solid fa-xmark" aria-hidden="true" />
          </button>
        </div>

        <div className="tabs" role="group" aria-label={t("crew.title")}>
          <button
            type="button"
            className={tab === "active" ? "on" : ""}
            onClick={() => setTab("active")}
          >
            {t("crew.tab.active")} ({activeList.length})
          </button>
          <button
            type="button"
            className={tab === "archived" ? "on" : ""}
            onClick={() => setTab("archived")}
          >
            {t("crew.tab.archived")} ({archivedList.length})
          </button>
        </div>

        {tab === "active" ? (
          <div className="crew-list">
            {activeList.length === 0 && <div className="empty">{t("crew.empty")}</div>}
            {activeList.map((item) => (
              <div key={item.code} className="crew-row">
                <div>
                  <b>{item.code}</b>{" "}
                  <small>
                    {item.name}
                    {item.age !== null ? ` · ${t("profile.age", { age: item.age })}` : ""}
                    {item.sex ? ` · ${t(`sex.${item.sex}`)}` : ""}
                  </small>
                </div>
                <div className="crew-actions">
                  {confirming === item.code ? (
                    <>
                      <button
                        type="button"
                        className="danger"
                        disabled={busy}
                        onClick={() => archiveMutation.mutate(item.code)}
                      >
                        {t("crew.confirm")}
                      </button>
                      <button type="button" onClick={() => setConfirming(null)}>
                        {t("crew.cancel")}
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="danger"
                      disabled={busy || activeList.length <= 1}
                      onClick={() => {
                        setError(null);
                        setConfirming(item.code);
                      }}
                      title={
                        activeList.length <= 1 ? t("crew.last_hint") : t("crew.archive")
                      }
                    >
                      {t("crew.archive")}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <>
            <p className="hint">{t("crew.archived_hint")}</p>
            <div className="crew-list">
              {archivedList.length === 0 && <div className="empty">{t("crew.empty")}</div>}
              {archivedList.map((item) => (
                <div key={item.code} className="crew-row">
                  <div>
                    <b>{item.code}</b> <small>{item.name}</small>
                  </div>
                  <div className="crew-actions">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => restoreMutation.mutate(item.code)}
                    >
                      {t("crew.restore")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <section className="crew-add">
          <h3>{t("crew.add")}</h3>
          <div className="row2">
            <div className="field">
              <label htmlFor="crew-code">{t("crew.code")}</label>
              <input
                id="crew-code"
                type="text"
                maxLength={32}
                placeholder="AST-03"
                value={code}
                onChange={(event) => setCode(event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="crew-name">{t("crew.name")}</label>
              <input
                id="crew-name"
                type="text"
                maxLength={120}
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>
          </div>
          <div className="row2">
            <div className="field">
              <label htmlFor="crew-sex">{t("crew.sex")}</label>
              <select
                id="crew-sex"
                value={sex}
                onChange={(event) => setSex(event.target.value as Sex)}
              >
                <option value="male">{t("sex.male")}</option>
                <option value="female">{t("sex.female")}</option>
              </select>
            </div>
            <TemporalField
              id="crew-birth"
              label={t("crew.birth")}
              mode="date"
              value={birthDate}
              max={todayISO()}
              onChange={setBirthDate}
            />
          </div>
          <p className="crew-error" role="alert">
            {error ?? ""}
          </p>
          <div className="actions">
            <button
              type="button"
              className="primary"
              disabled={busy || !code.trim() || !birthDate}
              onClick={() => {
                setError(null);
                createMutation.mutate();
              }}
            >
              {createMutation.isPending ? t("crew.creating") : t("crew.create")}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
