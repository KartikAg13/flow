export type RiskBand = "low" | "medium" | "high";

export function riskBand(risk: number): RiskBand {
  if (risk >= 60) return "high";
  if (risk >= 35) return "medium";
  return "low";
}

export function riskLabel(band: RiskBand): string {
  if (band === "high") return "Elevated";
  if (band === "medium") return "Watch";
  return "Nominal";
}

export function timeAgo(iso: string, nowMs: number): string {
  const mins = Math.round((nowMs - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export const pct = (share: number) => `${Math.round(share * 100)}%`;
export const mmt = (v: number) => (v >= 10 ? v.toFixed(0) : v.toFixed(1));
// Tonnes in one unit across the scenario card: 54, 7.2, 0.36 MMT
export const tonnes = (mmtValue: number) => mmtValue.toFixed(mmtValue >= 10 ? 0 : mmtValue >= 1 ? 1 : 2);
// Head counts the Indian way: 58.3 lakh, 3.4 crore
export const count = (n: number) =>
  n >= 1e7 ? `${(n / 1e7).toFixed(1)} crore` : n >= 1e5 ? `${(n / 1e5).toFixed(1)} lakh` : n.toLocaleString("en-IN");
