import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, Tooltip } from "react-leaflet";
import L from "leaflet";
import { commodityLabels, type Dashboard } from "../api";
import { useDarkMode } from "../hooks/usePoll";
import { mmt, riskBand } from "../utils/risk";

interface MapPanelProps {
  dashboard: Dashboard;
  selectedId: string;
  marked: Set<string>; // "kind:id" places the Copilot named, drawn red for a while
  onSelect: (id: string) => void;
}

const FACILITY_LABEL = {
  refinery: "Refinery",
  lng_terminal: "LNG terminal",
  fertilizer_plant: "Fertilizer plant",
  spr: "Strategic petroleum reserve",
};

const PIPE_UNIT = { mmtpa: "MMT a year", mmscmd: "million m³ a day", mbpd: "million barrels a day" };

// Every tracked chokepoint, Cape of Good Hope to Malacca, plus India's coasts.
const BOUNDS: L.LatLngBoundsExpression = [
  [-36, 14],
  [33, 104],
];

function diamond(band: string, active: boolean, marked: boolean) {
  const size = active ? 22 : 16;
  return L.divIcon({
    className: "cp-marker-wrap",
    html: `<span class="cp-marker cp-marker--${band}${active ? " is-active" : ""}${marked ? " is-marked" : ""}"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function MapPanel({ dashboard, selectedId, marked, onSelect }: MapPanelProps) {
  const dark = useDarkMode();
  const cps = Object.fromEntries(dashboard.chokepoints.map((c) => [c.id, c]));
  const ports = Object.fromEntries(dashboard.ports.map((p) => [p.id, p]));
  const tiles = dark ? "World_Dark_Gray_Base" : "World_Light_Gray_Base";

  return (
    <section className="panel map-panel" aria-label="Map of corridors to India">
      <header className="panel__header">
        <h2>Corridors to India</h2>
        <span className="panel__hint">Line width shows tonnes per year</span>
      </header>
      <div className="map-panel__canvas">
        <MapContainer bounds={BOUNDS} minZoom={2} maxZoom={7} worldCopyJump>
          <TileLayer
            key={tiles}
            attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
            url={`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/${tiles}/MapServer/tile/{z}/{y}/{x}`}
          />

          {dashboard.lanes.map((lane) => {
            const cp = cps[lane.chokepoint];
            const port = ports[lane.port];
            const active = lane.chokepoint === selectedId;
            // Leaflet reads className only when a path is created (react-leaflet's pathOptions
            // go through setStyle, which ignores it), so it is a creation prop and part of the key.
            const hit = marked.has(`chokepoint:${lane.chokepoint}`) ? " is-marked" : "";
            const cls = `lane lane--${riskBand(cp.risk)}${active ? " is-active" : ""}${hit}`;
            return (
              <Polyline
                key={`${lane.chokepoint}-${lane.port}-${cls}`}
                className={cls}
                positions={[
                  [cp.lat, cp.lon],
                  [port.lat, port.lon],
                ]}
                pathOptions={{ weight: 1 + Math.sqrt(lane.mmt) / 1.6 }}
                eventHandlers={{ click: () => onSelect(cp.id) }}
              >
                <Tooltip sticky className="flow-tooltip">
                  {cp.name} → {port.name}: {mmt(lane.mmt)} MMT a year of{" "}
                  {lane.commodities.map((c) => commodityLabels[c]).join(", ")}
                </Tooltip>
              </Polyline>
            );
          })}

          {dashboard.pipelines.map((p) => {
            const cls = `pipeline pipeline--${p.fluid}${p.scope === "bypass" ? " pipeline--bypass" : ""}`;
            return (
              <Polyline key={`${p.id}-${cls}`} className={cls} positions={p.points} pathOptions={{ weight: 2 }}>
                <Tooltip sticky className="flow-tooltip">
                  {p.name} · {p.operator} · {p.capacity} {PIPE_UNIT[p.capacity_unit]}
                  {p.status !== "operational" ? ` · ${p.status}` : ""}
                </Tooltip>
              </Polyline>
            );
          })}

          {dashboard.facilities.map((f) => {
            const hit = marked.has(`${f.kind}:${f.id}`);
            const cls = `facility facility--${f.kind}${hit ? " is-marked" : ""}`;
            return (
              <CircleMarker key={`${f.kind}-${f.id}-${cls}`} className={cls} center={[f.lat, f.lon]} radius={hit ? 5 : f.kind === "spr" ? 4 : 2.5}>
                <Tooltip className="flow-tooltip">
                  {f.name} · {FACILITY_LABEL[f.kind]}
                </Tooltip>
              </CircleMarker>
            );
          })}

          {dashboard.ports.map((p) => {
            const hit = marked.has(`port:${p.id}`);
            const cls = `port${hit ? " is-marked" : ""}`;
            return (
              <CircleMarker key={`${p.id}-${cls}`} className={cls} center={[p.lat, p.lon]} radius={hit ? 6 : 3.5}>
                <Tooltip className="flow-tooltip">
                  {p.name} port
                  {Object.entries(p.exposure).map(([c, v]) => ` · ${commodityLabels[c as keyof typeof commodityLabels]} ${mmt(v.mmt)} MMT`)}
                </Tooltip>
              </CircleMarker>
            );
          })}

          {dashboard.chokepoints.map((cp) => (
            <Marker
              key={cp.id}
              position={[cp.lat, cp.lon]}
              icon={diamond(riskBand(cp.risk), cp.id === selectedId, marked.has(`chokepoint:${cp.id}`))}
              title={cp.name}
              eventHandlers={{ click: () => onSelect(cp.id) }}
            >
              <Tooltip direction="top" offset={[0, -8]} className="flow-tooltip">
                {cp.name} · risk {cp.risk}
              </Tooltip>
            </Marker>
          ))}
        </MapContainer>
      </div>
      <footer className="legend">
        <span><i className="swatch swatch--diamond" /> Chokepoint</span>
        <span><i className="swatch swatch--port" /> Indian port</span>
        <span><i className="swatch swatch--facility" /> Refinery, terminal or plant</span>
        <span><i className="swatch swatch--spr" /> Strategic reserve</span>
        <span><i className="swatch swatch--pipe-crude" /> Oil pipeline</span>
        <span><i className="swatch swatch--pipe-gas" /> Gas pipeline</span>
        <span className="legend__bands">
          <i className="swatch swatch--high" /> Elevated <i className="swatch swatch--medium" /> Watch{" "}
          <i className="swatch swatch--low" /> Nominal
        </span>
      </footer>
    </section>
  );
}
