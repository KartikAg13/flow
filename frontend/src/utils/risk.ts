export type RiskBand = "low" | "medium" | "high";

export function riskBand(risk: number): RiskBand {
  if (risk >= 60) return "high";
  if (risk >= 35) return "medium";
  return "low";
}

export const riskColor: Record<RiskBand, string> = {
  high: "#c0524a",
  medium: "#d4a24c",
  low: "#4c9a7e",
};

export function riskLabel(band: RiskBand): string {
  if (band === "high") return "Elevated";
  if (band === "medium") return "Watch";
  return "Nominal";
}

export function timeAgo(iso: string, nowMs: number): string {
  const diffMs = nowMs - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return `${days}d ago`;
}
