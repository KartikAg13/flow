import { useEffect, useState } from "react";
import { newsFeed, chokepoints, commodityLabels } from "../data/staticData";
import { timeAgo } from "../utils/risk";

interface NewsPanelProps {
  selectedId: string;
  onSelect: (id: string) => void;
}

const cpName = (id: string | null) => chokepoints.find((c) => c.id === id)?.name ?? null;

export default function NewsPanel({ selectedId, onSelect }: NewsPanelProps) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="news-panel">
      <div className="panel-header">
        <h2>Current news</h2>
        <span className="dot dot--live" />
      </div>
      <div className="news-panel__list thin-scroll">
        {newsFeed.map((item) => {
          const name = cpName(item.chokepointId);
          const related = item.chokepointId === selectedId;
          return (
            <article
              key={item.id}
              className={`news-item news-item--${item.sentiment}${related ? " news-item--related" : ""}`}
              onClick={() => item.chokepointId && onSelect(item.chokepointId)}
              role={item.chokepointId ? "button" : undefined}
            >
              <div className="news-item__meta">
                <span className={`news-item__sentiment news-item__sentiment--${item.sentiment}`}>
                  {item.sentiment}
                </span>
                <span className="news-item__time">{timeAgo(item.timestamp, now)}</span>
              </div>
              <p className="news-item__headline">{item.headline}</p>
              <div className="news-item__tags">
                <span className="news-item__source">{item.source}</span>
                {name && <span className="news-item__tag">{name}</span>}
                {item.commodity && <span className="news-item__tag news-item__tag--muted">{commodityLabels[item.commodity]}</span>}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
