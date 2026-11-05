import { useCallback, useRef, useState } from "react";
import { api, type Place } from "./api";
import { usePoll } from "./hooks/usePoll";
import TopBar from "./components/TopBar";
import RiskShower from "./components/RiskShower";
import MapPanel from "./components/MapPanel";
import NewsPanel from "./components/NewsPanel";
import InfoPanel from "./components/InfoPanel";
import CopilotSheet, { type ScenarioRequest } from "./components/CopilotSheet";

const MARK_MS = 3 * 60_000; // Copilot places stay red this long, or until the next question

export default function App() {
  const { data, error } = usePoll(api.dashboard, 60_000);
  const [selectedId, setSelectedId] = useState("hormuz");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [scenario, setScenario] = useState<ScenarioRequest | null>(null);
  const askButton = useRef<HTMLButtonElement>(null);
  const [marked, setMarked] = useState<Set<string>>(new Set());
  const unmark = useRef<number>();

  const markPlaces = useCallback((places: Place[]) => {
    window.clearTimeout(unmark.current);
    setMarked(new Set(places.map((p) => `${p.kind}:${p.id}`)));
    if (places.length) unmark.current = window.setTimeout(() => setMarked(new Set()), MARK_MS);
  }, []);

  const closeSheet = useCallback(() => {
    setSheetOpen(false);
    askButton.current?.focus();
  }, []);

  if (!data) {
    return (
      <div className="splash" role="status">
        <span className="splash__mark">Flow</span>
        <p>{error ? `Can't reach the Flow API (${error}). Start it with: uv run flow serve` : "Loading…"}</p>
      </div>
    );
  }

  const selected = data.chokepoints.find((c) => c.id === selectedId) ?? data.chokepoints[0];

  return (
    <div className="shell">
      <TopBar
        asOf={data.as_of}
        events={data.events}
        offline={error}
        askRef={askButton}
        askOpen={sheetOpen}
        onAsk={() => (sheetOpen ? closeSheet() : setSheetOpen(true))}
      />
      <RiskShower chokepoints={data.chokepoints} selectedId={selected.id} onSelect={setSelectedId} />
      <main className="shell__main">
        <MapPanel dashboard={data} selectedId={selected.id} marked={marked} onSelect={setSelectedId} />
        <NewsPanel chokepoint={selected} chokepoints={data.chokepoints} onSelect={setSelectedId} />
      </main>
      <InfoPanel
        chokepoint={selected}
        ports={data.ports}
        onSimulate={(months) => {
          setScenario({ chokepoint: selected.id, name: selected.name, months, at: Date.now() });
          setSheetOpen(true);
        }}
      />
      <CopilotSheet open={sheetOpen} scenario={scenario} onClose={closeSheet} onPlaces={markPlaces} />
    </div>
  );
}
