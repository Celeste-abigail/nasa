import { useId } from "react";

interface Props {
  severity: number;
  title: string;
  items: string[];
  note?: string | null;
  badge?: string;
}

export function RecommendationPanel({ severity, title, items, note, badge }: Props) {
  const id = useId().replace(/[:]/g, "");
  const level = Math.max(0, Math.min(4, Math.round(severity)));
  const alert = level >= 2;

  return (
    <section className={`recommendation-panel s${level}`} aria-labelledby={`rec-${id}`}>
      <div className="recommendation-head">
        <i
          className={`fa-solid ${alert ? "fa-triangle-exclamation" : "fa-circle-check"}`}
          aria-hidden="true"
        />
        <h2 id={`rec-${id}`}>{title}</h2>
        {badge ? <span className="badge recommendation-badge">{badge}</span> : null}
      </div>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {note ? <p className="hint">{note}</p> : null}
    </section>
  );
}
