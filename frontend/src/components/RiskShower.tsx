import type { Chokepoint } from "../data/staticData";
import { riskBand, riskColor, riskLabel } from "../utils/risk";
import Sparkline from "./Sparkline";

interface RiskShowerProps {
  chokepoints: Chokepoint[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export default function RiskShower({ chokepoints, selectedId, onSelect }: RiskShowerProps) {
  return (
    <section className="risk-shower" aria-label="Live chokepoint risk levels">
      <div className="risk-shower__label">
        <span className="dot dot--live" />
        live risk
      </div>
      <div className="risk-shower__dials thin-scroll">
        {chokepoints.map((cp) => {
          const band = riskBand(cp.risk);
          const color = riskColor[band];
          const active = cp.id === selectedId;
          const trendUp = cp.trend > 0;
          const trendFlat = cp.trend === 0;

          return (
            <button
              key={cp.id}
              className={`dial${active ? " dial--active" : ""}`}
              style={{ ["--dial-color" as any]: color }}
              onClick={() => onSelect(cp.id)}
              aria-pressed={active}
            >
              <div className="dial__top">
                <span className="dial__name">{cp.name}</span>
                <span className="dial__band" style={{ color }}>
                  {riskLabel(band)}
                </span>
              </div>
              <div className="dial__mid">
                <span className="dial__score">{cp.risk}</span>
                <span
                  className={`dial__trend${trendFlat ? " dial__trend--flat" : trendUp ? " dial__trend--up" : " dial__trend--down"}`}
                >
                  {trendFlat ? "→" : trendUp ? "▲" : "▼"} {Math.abs(cp.trend)}
                </span>
              </div>
              <Sparkline values={cp.history} color={color} />
            </button>
          );
        })}
      </div>
    </section>
  );
}
