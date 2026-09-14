import { MapContainer, TileLayer, Marker, Polyline, Popup, Tooltip } from "react-leaflet";
import L from "leaflet";
import type { Chokepoint, Port } from "../data/staticData";
import { riskBand, riskColor } from "../utils/risk";

interface MapPanelProps {
  chokepoints: Chokepoint[];
  ports: Port[];
  selectedId: string;
  onSelect: (id: string) => void;
}

function chokepointIcon(color: string, active: boolean) {
  const size = active ? 22 : 16;
  return L.divIcon({
    className: "chokepoint-marker-wrap",
    html: `<span class="chokepoint-marker${active ? " chokepoint-marker--active" : ""}" style="--c:${color}"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

const portIcon = L.divIcon({
  className: "port-marker-wrap",
  html: `<span class="port-marker"></span>`,
  iconSize: [7, 7],
  iconAnchor: [3.5, 3.5],
});

export default function MapPanel({ chokepoints, ports, selectedId, onSelect }: MapPanelProps) {
  const byId = Object.fromEntries(chokepoints.map((c) => [c.id, c]));

  return (
    <section className="map-panel">
      <div className="panel-header">
        <h2>Chokepoint map</h2>
        <span className="panel-header__hint">India-bound crude, LNG &amp; fertilizer corridors</span>
      </div>
      <div className="map-panel__canvas">
        <MapContainer
          center={[15, 62]}
          zoom={3}
          minZoom={2}
          maxZoom={7}
          scrollWheelZoom={true}
          worldCopyJump
          style={{ height: "100%", width: "100%", background: "var(--ink-900)" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
          />

          {ports.map((port) =>
            port.routesVia.map((cpId) => {
              const cp = byId[cpId];
              if (!cp) return null;
              const band = riskBand(cp.risk);
              return (
                <Polyline
                  key={`${port.id}-${cpId}`}
                  positions={[
                    [port.lat, port.lon],
                    [cp.lat, cp.lon],
                  ]}
                  pathOptions={{
                    color: riskColor[band],
                    weight: cpId === selectedId ? 1.4 : 0.6,
                    opacity: cpId === selectedId ? 0.55 : 0.16,
                    dashArray: "1 5",
                  }}
                />
              );
            })
          )}

          {ports.map((port) => (
            <Marker key={port.id} position={[port.lat, port.lon]} icon={portIcon}>
              <Tooltip direction="top" offset={[0, -4]} className="flow-tooltip">
                {port.name}
              </Tooltip>
            </Marker>
          ))}

          {chokepoints.map((cp) => {
            const band = riskBand(cp.risk);
            const color = riskColor[band];
            const active = cp.id === selectedId;
            return (
              <Marker
                key={cp.id}
                position={[cp.lat, cp.lon]}
                icon={chokepointIcon(color, active)}
                eventHandlers={{ click: () => onSelect(cp.id) }}
              >
                <Popup className="flow-popup">
                  <strong>{cp.name}</strong>
                  <br />
                  {cp.transitVolume} {cp.transitUnit} transit · risk {cp.risk}
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
      <div className="map-panel__legend">
        <span>
          <i className="legend-swatch legend-swatch--diamond" /> chokepoint
        </span>
        <span>
          <i className="legend-swatch legend-swatch--dot" /> Indian port
        </span>
        <span>
          <i className="legend-swatch legend-swatch--high" /> elevated
        </span>
        <span>
          <i className="legend-swatch legend-swatch--medium" /> watch
        </span>
        <span>
          <i className="legend-swatch legend-swatch--low" /> nominal
        </span>
      </div>
    </section>
  );
}
