import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  astronaut: string;
  lang: string;
}

interface Item {
  group: "summary" | "data";
  icon: string;
  label: string;
  href: string;
  external?: boolean;
}

export function DownloadMenu({ astronaut, lang }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const lastAstronaut = useRef(astronaut);

  useEffect(() => {
    if (!open) return;

    const onPointer = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  useEffect(() => {
    if (lastAstronaut.current !== astronaut && lastAstronaut.current !== "") {
      lastAstronaut.current = astronaut;
      setOpen(false);
    }
    lastAstronaut.current = astronaut;
  }, [astronaut]);

  const base = `/api/v1/astronauts/${encodeURIComponent(astronaut)}/export`;
  const suffix = `?lang=${encodeURIComponent(lang)}`;

  const items: Item[] = [
    {
      group: "summary",
      icon: "fa-file-lines",
      label: t("downloads.summary_html"),
      href: `${base}/summary.html${suffix}`,
      external: true,
    },
    {
      group: "summary",
      icon: "fa-file-pdf",
      label: t("downloads.summary_pdf"),
      href: `${base}/summary.pdf${suffix}`,
    },
    {
      group: "summary",
      icon: "fa-file-code",
      label: t("downloads.summary_json"),
      href: `${base}/summary.json${suffix}`,
    },
    {
      group: "data",
      icon: "fa-file-csv",
      label: t("downloads.data_csv"),
      href: `${base}/data.csv${suffix}`,
    },
    {
      group: "data",
      icon: "fa-database",
      label: t("downloads.data_json"),
      href: `${base}/data.json${suffix}`,
    },
  ];

  const groups: Array<{ key: Item["group"]; label: string }> = [
    { key: "summary", label: t("downloads.group_summary") },
    { key: "data", label: t("downloads.group_data") },
  ];

  return (
    <div className="download-menu" ref={rootRef}>
      <button
        type="button"
        className="compact-download"
        disabled={!astronaut}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        title={t("downloads.button")}
      >
        <i className="fa-solid fa-download" aria-hidden="true" />
        <span>{t("downloads.button")}</span>
        <i className="fa-solid fa-chevron-down chevron" aria-hidden="true" />
      </button>

      {open && (
        <div className="download-dropdown" role="menu">
          {groups.map((group) => (
            <div key={group.key}>
              <p className="download-group">{group.label}</p>
              {items
                .filter((item) => item.group === group.key)
                .map((item) => (
                  <a
                    key={item.href}
                    role="menuitem"
                    href={item.href}
                    target={item.external ? "_blank" : undefined}
                    rel={item.external ? "noreferrer" : undefined}
                    onClick={() => setOpen(false)}
                  >
                    <i className={`fa-solid ${item.icon}`} aria-hidden="true" />
                    {item.label}
                  </a>
                ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
