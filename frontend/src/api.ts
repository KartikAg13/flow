// Typed client for the Python API (src/flow/api.py). In dev, Vite proxies /api to :8000.

export type Commodity = "crude_oil" | "lng" | "urea" | "dap" | "mop";
export type Exposure = Partial<Record<Commodity, { mmt: number; share: number }>>;

export interface Chokepoint {
  id: string;
  name: string;
  lat: number;
  lon: number;
  transit_volume: number;
  transit_unit: string;
  year: number;
  source: string;
  source_url: string;
  risk: number;
  history: number[];
  exposure: Exposure;
  ports: string[];
}

export interface Port {
  id: string;
  name: string;
  lat: number;
  lon: number;
  coast: "west" | "east";
  via: string[];
  exposure: Exposure;
}

export interface Lane {
  chokepoint: string;
  port: string;
  mmt: number;
  commodities: Commodity[];
}

export interface Facility {
  id: string;
  name: string;
  lat: number;
  lon: number;
  kind: "refinery" | "lng_terminal" | "fertilizer_plant" | "spr";
}

export interface Pipeline {
  id: string;
  name: string;
  fluid: "crude" | "gas";
  scope: "bypass" | "domestic";
  operator: string;
  capacity: number;
  capacity_unit: "mmtpa" | "mmscmd" | "mbpd";
  status: string;
  points: [number, number][];
}

export interface Dashboard {
  as_of: string | null;
  events: number;
  chokepoints: Chokepoint[];
  ports: Port[];
  lanes: Lane[];
  facilities: Facility[];
  pipelines: Pipeline[];
}

export interface NewsItem {
  event_id: string;
  observed_at: string;
  source_name: string;
  url: string;
  title: string;
  tone: number;
  entities: string[];
  commodities: Commodity[];
}

interface Lost {
  id: string;
  name: string;
  state: string;
  lost_mmt: number;
}

export interface StateShort {
  state: string;
  diesel_kt: number;
  petrol_kt: number;
  fertilizer_kt: number;
  farm_holdings: number;
}

export interface FuelShort {
  short_mmt: number;
  share_of_use: number;
  days_of_use_lost: number;
  segments: { segment: string; kt: number }[];
}

// sim.impact: where a closure lands and who runs short (src/flow/sim/__init__.py)
export interface Impact {
  states_hit: { state: string; lost_mmt: number; by: Record<string, number> }[];
  fuel_short_states: StateShort[];
  farm_short_states: StateShort[];
  fuel: { diesel: FuelShort; petrol: FuelShort };
  fertilizer: Record<"urea" | "dap" | "mop", { short_mmt: number; share_of_use: number }>;
  farm_holdings_affected: number;
  city_gas_lost_mmt_lng: number;
  power_gas_lost_mmt_lng: number;
  urea_plants: { output_lost_share: number; plants: { name: string; state: string }[] };
  assumption: string;
}

// sim.reroute: sea detours, bypass pipelines, stranded cargo, open entry points
export interface Reroutes {
  detours: { supplier: string; commodity: Commodity; to: string; mmt: number; via: string[]; extra_nm: number; extra_days: number; recovered_mmt: number }[];
  bypasses: { pipeline: string; supplier: string; outlet: string; via: string[]; mmt: number; of_blocked_mmt: number; extra_days: number; recovered_mmt: number }[];
  stranded: { supplier: string; commodity: Commodity; mmt: number; reason: string }[];
  recovered: { commodity: Commodity; lost_mmt: number; recovered_mmt: number; still_lost_mmt: number }[];
  entry_points: { site: string; state: string; fluid: "crude" | "gas"; pipeline: string; reaches: string[] }[];
  assumption: string;
}

export interface Scenario {
  closed: string[];
  months: number;
  commodities: { commodity: Commodity; lost_mmt: number; share_of_imports: number }[];
  ports: Lost[];
  facilities: Lost[];
  downstream: { from: string; pipeline: string; sites: { name: string; state: string }[] }[];
  cascade: { lng_lost_mmt: number; fertilizer_gas_lost_mmt_lng: number; urea_output_at_risk_mmt: number };
  spr: { capacity_mmt: number; days_of_lost_crude_covered: number | null; sites: string[] };
  alternatives: Partial<Record<Commodity, { supplier: string; mmt_per_year: number; via: string[] }[]>>;
  assumption: string;
  impact: Impact;
  reroutes: Reroutes;
}

export interface Place {
  kind: "chokepoint" | "port" | Facility["kind"];
  id: string;
  name: string;
}

export interface Answer {
  answer: string; // plain-text rendering, as the CLI prints it
  summary: string;
  points: string[];
  assumption: string;
  places: Place[];
  trace: string;
}

export const commodityLabels: Record<Commodity, string> = {
  crude_oil: "Crude oil",
  lng: "LNG",
  urea: "Urea",
  dap: "DAP",
  mop: "MOP",
};

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `Server returned ${res.status}`);
  return body as T;
}

export const api = {
  dashboard: () => call<Dashboard>("/api/dashboard"),
  news: (entity?: string) =>
    call<NewsItem[]>(`/api/news?limit=60${entity ? `&entity=${encodeURIComponent(entity)}` : ""}`),
  simulate: (chokepoint: string, months: number) =>
    call<Scenario>(`/api/sim?chokepoints=${encodeURIComponent(chokepoint)}&months=${months}`),
  ask: (question: string) =>
    call<Answer>("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};
