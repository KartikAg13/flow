import { useState } from "react";
import { api, commodityLabels, type Chokepoint } from "../api";
import { usePoll } from "../hooks/usePoll";
import { timeAgo } from "../utils/risk";

interface NewsPanelProps {
  chokepoint: Chokepoint;
  chokepoints: Chokepoint[];
  onSelect: (id: string) => void;
}

const toneClass = (tone: number) => (tone <= -3 ? "negative" : tone <= -1 ? "mixed" : "neutral");

export default function NewsPanel({ chokepoint, chokepoints, onSelect }: NewsPanelProps) {
  const [scope, setScope] = useState<"selected" | "all">("selected");
  const entity = scope === "selected" ? chokepoint.id : undefined;
  const { data, error } = usePoll(() => api.news(entity), 60_000, entity ?? "all");
  const names = Object.fromEntries(chokepoints.map((c) => [c.id, c.name]));
  const now = Date.now();

  return (
    <section className="panel news-panel" aria-label="News">
      <header className="panel__header">
        <h2>News</h2>
        <div className="segmented" role="group" aria-label="Which news">
          <button aria-pressed={scope === "selected"} onClick={() => setScope("selected")}>
            {chokepoint.name.replace(/^Strait of /, "")}
          </button>
          <button aria-pressed={scope === "all"} onClick={() => setScope("all")}>
            All
          </button>
        </div>
      </header>
      <ol className="news-list">
        {!data && <li className="news-list__empty">{error ?? "Loading…"}</li>}
        {data?.length === 0 && (
          <li className="news-list__empty">
            No stored GDELT articles mention {chokepoint.name}. That is why its risk reads low.
          </li>
        )}
        {data?.map((item) => (
          <li key={item.event_id} className="news-item">
            <a className="news-item__title" href={item.url} target="_blank" rel="noopener noreferrer">
              {item.title}
            </a>
            <div className="news-item__meta">
              <span className={`tone tone--${toneClass(item.tone)}`} title="GDELT tone: below 0 is negative coverage">
                tone {item.tone}
              </span>
              <span>{item.source_name}</span>
              <span>{timeAgo(item.observed_at, now)}</span>
            </div>
            <div className="news-item__tags">
              {item.entities
                .filter((e) => names[e])
                .map((e) => (
                  <button key={e} className="chip chip--link" onClick={() => onSelect(e)}>
                    {names[e]}
                  </button>
                ))}
              {item.commodities.map((c) => (
                <span key={c} className="chip">
                  {commodityLabels[c]}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
