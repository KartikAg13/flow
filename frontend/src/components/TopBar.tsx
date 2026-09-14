import { useEffect, useState } from "react";

export default function TopBar() {
  const [clock, setClock] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const utc = clock.toISOString().slice(11, 19);

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <span className="topbar__mark">FLOW</span>
        <span className="topbar__tagline">critical-import chokepoint instrument</span>
      </div>

      <div className="topbar__meta">
        <div className="topbar__status" title="This build renders seed data locally; no live backend is connected yet.">
          <span className="dot dot--brass" />
          local data · backend not connected
        </div>
        <div className="topbar__clock">
          <span className="topbar__clock-label">UTC</span>
          <span className="topbar__clock-value">{utc}</span>
        </div>
      </div>
    </header>
  );
}
