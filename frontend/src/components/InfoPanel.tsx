import type { Chokepoint, Port } from "../data/staticData";
import { riskBand, riskColor, riskLabel } from "../utils/risk";

interface InfoPanelProps {
  chokepoint: Chokepoint;
  ports: Port[];
  totalVolume: number;
}

export default function InfoPanel({ chokepoint, ports, totalVolume }: InfoPanelProps) {
  const band = riskBand(chokepoint.risk);
  const color = riskColor[band];
  const servedPorts = ports.filter((p) => p.routesVia.includes(chokepoint.id));

  return (
    <section className="info-panel">
      <div className="info-panel__detail">
        <div className="info-panel__title-row">
          <h2>{chokepoint.name}</h2>
          <span className="info-panel__band" style={{ color, borderColor: color }}>
            {riskLabel(band)} · {chokepoint.risk}
          </span>
        </div>
        <p className="info-panel__summary">{chokepoint.summary}</p>
        <div className="info-panel__factors">
          {chokepoint.watchFactors.map((f) => (
            <span key={f} className="factor-chip">
              {f}
            </span>
          ))}
        </div>
      </div>

      <div className="info-panel__stats">
        <div className="stat">
          <span className="stat__value">
            {chokepoint.transitVolume} <small>{chokepoint.transitUnit}</small>
          </span>
          <span className="stat__label">transit volume, {chokepoint.year}</span>
        </div>
        <div className="stat">
          <span className="stat__value">{servedPorts.length}</span>
          <span className="stat__label">Indian ports routed via this point</span>
        </div>
        <div className="stat">
          <span className="stat__value">
            {totalVolume.toFixed(1)} <small>mbpd</small>
          </span>
          <span className="stat__label">combined tracked chokepoint volume</span>
        </div>
        <div className="stat stat--source">
          <span className="stat__label stat__label--source">source</span>
          <span className="stat__source-text">{chokepoint.source}</span>
        </div>
      </div>
    </section>
  );
}
