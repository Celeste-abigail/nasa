import { useTranslation } from "react-i18next";

import { todayISO } from "../lib/format";
import { nowLocalInput, nowUtcInput } from "../lib/time";

interface Props {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  mode?: "date" | "datetime";
  utc?: boolean;
  optional?: boolean;
  hint?: string;
  max?: string;
}

export function TemporalField({
  id,
  label,
  value,
  onChange,
  mode = "datetime",
  utc = false,
  optional = false,
  hint,
  max,
}: Props) {
  const { t } = useTranslation();

  function setNow() {
    onChange(mode === "datetime" ? (utc ? nowUtcInput() : nowLocalInput()) : todayISO());
  }

  return (
    <div className="field temporal-field">
      <div className="temporal-label">
        <label htmlFor={id}>
          {label}
          {optional ? <span className="optional"> ({t("cortisol.optional")})</span> : null}
        </label>
        <button type="button" className="now-btn" onClick={setNow}>
          {t("temporal.now")}
        </button>
      </div>
      <input
        id={id}
        type={mode === "datetime" ? "datetime-local" : "date"}
        value={value}
        max={max}
        onChange={(event) => onChange(event.target.value)}
      />
      {hint ? <p className="hint">{hint}</p> : null}
    </div>
  );
}
