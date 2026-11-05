import { useState } from "react";
import { commodityLabels, type Chokepoint, type Commodity, type Port } from "../api";
import { mmt, pct, riskBand, riskLabel } from "../utils/risk";

interface InfoPanelProps {
  chokepoint: Chokepoint;
  ports: Port[];
  onSimulate: (months: number) => void;
}

const MONTHS = [1, 3, 6, 12];

export default function InfoPanel({ chokepoint, ports, onSimulate }: InfoPanelProps) {
  const [months, setMonths] = useState(6);
  const band = riskBand(chokepoint.risk);
  const rows = (Object.entries(chokepoint.exposure) as [Commodity, { mmt: number; share: number }][]).sort(
    (a, b) => b[1].share - a[1].share,
  );
  const portNames = chokepoint.ports.map((id) => ports.find((p) => p.id === id)?.name ?? id);

  return (
    <section className="panel info-panel" aria-label={`${chokepoint.name} details`}>
      <div className="info-panel__head">
        <div className="info-panel__title">
          <h2>{chokepoint.name}</h2>
          <span className={`badge badge--${band}`}>
            {riskLabel(band)} · {chokepoint.risk}
          </span>
        </div>
        <p className="muted">
          {chokepoint.transit_volume} {chokepoint.transit_unit} of oil transits here ({chokepoint.year}).{" "}
          <a href={chokepoint.source_url} target="_blank" rel="noopener noreferrer">
            EIA
          </a>
        </p>
        <p className="muted">
          {portNames.length ? `India-bound cargo lands at ${portNames.join(", ")}.` : "No tracked India-bound cargo."}
        </p>
      </div>

      <div className="exposure">
        <h3>Share of India's imports through here</h3>
        {rows.length === 0 && <p className="muted">None of the tracked import routes use it.</p>}
        {rows.map(([c, v]) => (
          <div className="exposure__row" key={c}>
            <span className="exposure__label">{commodityLabels[c]}</span>
            <span className="exposure__bar" aria-hidden="true">
              <span style={{ width: pct(v.share) }} />
            </span>
            <span className="exposure__value">
              {pct(v.share)} <small>{mmt(v.mmt)} MMT</small>
            </span>
          </div>
        ))}
      </div>

      <div className="simulate">
        <h3>What if it closes?</h3>
        <div className="segmented" role="radiogroup" aria-label="Closure length">
          {MONTHS.map((m) => (
            <button key={m} role="radio" aria-checked={months === m} onClick={() => setMonths(m)}>
              {m} mo
            </button>
          ))}
        </div>
        <button className="button button--tint" disabled={rows.length === 0} onClick={() => onSimulate(months)}>
          Simulate closure
        </button>
      </div>
    </section>
  );
}
