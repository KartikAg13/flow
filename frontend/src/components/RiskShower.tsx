import type { Chokepoint } from "../api";
import { riskBand, riskLabel } from "../utils/risk";
import Sparkline from "./Sparkline";

interface RiskShowerProps {
  chokepoints: Chokepoint[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export default function RiskShower({ chokepoints, selectedId, onSelect }: RiskShowerProps) {
  return (
    <section className="risk-row" aria-label="Live chokepoint risk">
      {chokepoints.map((cp) => {
        const band = riskBand(cp.risk);
        const prev = cp.history.length > 1 ? cp.history[cp.history.length - 2] : cp.risk;
        const delta = cp.risk - prev;
        return (
          <button
            key={cp.id}
            className={`dial dial--${band}`}
            aria-pressed={cp.id === selectedId}
            onClick={() => onSelect(cp.id)}
          >
            <span className="dial__name">{cp.name}</span>
            <span className="dial__row">
              <span className="dial__score">{cp.risk}</span>
              <span className="dial__band">{riskLabel(band)}</span>
            </span>
            <span className="dial__row">
              <Sparkline values={cp.history} />
              <span className="dial__trend" title="Change since the previous GDELT slice">
                {delta === 0 ? "steady" : `${delta > 0 ? "▲" : "▼"} ${Math.abs(delta)}`}
              </span>
            </span>
          </button>
        );
      })}
    </section>
  );
}
