import { useEffect, useRef, useState } from "react";
import { chokepoints as seedChokepoints, type Chokepoint } from "../data/staticData";

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

/**
 * Simulates a live telemetry feed on top of the static seed chokepoints.
 * No backend is connected yet — this jitters values locally so the
 * instrument panel behaves like a live system during frontend review.
 */
export function useLiveChokepoints(intervalMs = 4000) {
  const [data, setData] = useState<Chokepoint[]>(seedChokepoints);
  const [now, setNow] = useState<number>(Date.now());
  const tick = useRef(0);

  useEffect(() => {
    const id = setInterval(() => {
      tick.current += 1;
      setNow(Date.now());
      setData((prev) =>
        prev.map((cp) => {
          const jitter = (Math.random() - 0.5) * 5;
          const nextRisk = Math.round(clamp(cp.risk + jitter, 4, 96));
          const nextHistory = [...cp.history.slice(1), nextRisk];
          return {
            ...cp,
            risk: nextRisk,
            trend: nextRisk - nextHistory[0],
            history: nextHistory,
          };
        })
      );
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return { chokepoints: data, now };
}
