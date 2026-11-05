import type { RefObject } from "react";

interface TopBarProps {
  asOf: string | null;
  events: number;
  offline?: string;
  askOpen: boolean;
  askRef: RefObject<HTMLButtonElement>;
  onAsk: () => void;
}

export default function TopBar({ asOf, events, offline, askOpen, askRef, onAsk }: TopBarProps) {
  const stamp = asOf ? new Date(asOf).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "no news yet";

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <span className="topbar__mark">Flow</span>
        <span className="topbar__tagline">India's critical imports · crude, LNG, fertilizers</span>
      </div>
      <div className="topbar__meta">
        <span className={`status${offline ? " status--warn" : ""}`} role="status">
          <span className="status__dot" aria-hidden="true" />
          {offline ? "Offline · showing last data" : `GDELT ${stamp} · ${events.toLocaleString()} articles`}
        </span>
        <button
          ref={askRef}
          className="button button--tint"
          aria-expanded={askOpen}
          aria-controls="copilot"
          onClick={onAsk}
        >
          Ask Copilot
        </button>
      </div>
    </header>
  );
}
