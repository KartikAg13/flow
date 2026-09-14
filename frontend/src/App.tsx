import { useMemo, useState } from "react";
import TopBar from "./components/TopBar";
import RiskShower from "./components/RiskShower";
import MapPanel from "./components/MapPanel";
import NewsPanel from "./components/NewsPanel";
import InfoPanel from "./components/InfoPanel";
import { ports } from "./data/staticData";
import { useLiveChokepoints } from "./hooks/useLiveChokepoints";

export default function App() {
  const { chokepoints } = useLiveChokepoints();
  const [selectedId, setSelectedId] = useState("hormuz");

  const selected = useMemo(
    () => chokepoints.find((c) => c.id === selectedId) ?? chokepoints[0],
    [chokepoints, selectedId]
  );

  const totalVolume = useMemo(
    () => chokepoints.reduce((sum, c) => sum + c.transitVolume, 0),
    [chokepoints]
  );

  return (
    <div className="shell">
      <TopBar />
      <RiskShower chokepoints={chokepoints} selectedId={selectedId} onSelect={setSelectedId} />
      <main className="shell__main">
        <MapPanel chokepoints={chokepoints} ports={ports} selectedId={selectedId} onSelect={setSelectedId} />
        <NewsPanel selectedId={selectedId} onSelect={setSelectedId} />
      </main>
      <InfoPanel chokepoint={selected} ports={ports} totalVolume={totalVolume} />
    </div>
  );
}
