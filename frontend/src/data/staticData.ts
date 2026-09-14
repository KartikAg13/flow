// Data sourced from data/seeds/*.json (chokepoints.json, ports.json, suppliers.json).
// This module stands in for live SQLite/API data until the backend is wired up.
// Risk scores, trends, and news below are illustrative placeholders, not live intel.

export type Commodity = "crude_oil" | "lng" | "urea" | "dap" | "mop";

export interface Chokepoint {
  id: string;
  name: string;
  lat: number;
  lon: number;
  transitVolume: number;
  transitUnit: string;
  year: number;
  source: string;
  /** 0-100 composite risk score (mock, for now derived from a seeded formula) */
  risk: number;
  trend: number; // change vs 24h ago, can be negative
  history: number[]; // last 12 samples, oldest first
  summary: string;
  watchFactors: string[];
}

export interface Port {
  id: string;
  name: string;
  lat: number;
  lon: number;
  coast: "west" | "east";
  commodities: Commodity[];
  /** chokepoint ids this port's cargo typically routes through */
  routesVia: string[];
}

export interface Supplier {
  iso: string;
  name: string;
}

export interface NewsItem {
  id: string;
  timestamp: string; // ISO
  headline: string;
  source: string;
  chokepointId: string | null;
  commodity: Commodity | null;
  sentiment: "elevated" | "watch" | "routine";
}

export const commodityLabels: Record<Commodity, string> = {
  crude_oil: "Crude oil",
  lng: "LNG",
  urea: "Urea",
  dap: "DAP",
  mop: "MOP",
};

export const chokepoints: Chokepoint[] = [
  {
    id: "hormuz",
    name: "Strait of Hormuz",
    lat: 26.5667,
    lon: 56.25,
    transitVolume: 20.9,
    transitUnit: "mbpd",
    year: 2025,
    source: "EIA World Oil Transit Chokepoints, 1H25 avg.",
    risk: 71,
    trend: 6,
    history: [52, 54, 55, 58, 57, 61, 63, 65, 66, 68, 70, 71],
    summary:
      "Sole seaway for Gulf crude and the bulk of India's Saudi, Iraqi, and UAE barrels. Iran-linked naval posturing and insurance-market chatter are the two indicators traders watch here.",
    watchFactors: ["Naval activity near Bandar Abbas", "Tanker war-risk premiums", "Iran–US signalling"],
  },
  {
    id: "malacca",
    name: "Strait of Malacca",
    lat: 2.5,
    lon: 101.27,
    transitVolume: 23.2,
    transitUnit: "mbpd",
    year: 2025,
    source: "EIA World Oil Transit Chokepoints, 1H25 avg.",
    risk: 34,
    trend: -2,
    history: [40, 39, 38, 37, 38, 36, 35, 36, 34, 35, 36, 34],
    summary:
      "Longest single corridor by volume; mostly a downstream artery for onward Asian trade rather than India-bound cargo. Baseline risk is piracy and congestion, not geopolitics.",
    watchFactors: ["Singapore Strait congestion", "Piracy incidents, Riau Islands", "Typhoon season routing"],
  },
  {
    id: "bab_el_mandeb",
    name: "Bab el-Mandeb",
    lat: 12.5833,
    lon: 43.3333,
    transitVolume: 4.2,
    transitUnit: "mbpd",
    year: 2025,
    source: "EIA World Oil Transit Chokepoints, 1H25 avg.",
    risk: 58,
    trend: 3,
    history: [61, 63, 60, 58, 57, 55, 54, 56, 57, 55, 56, 58],
    summary:
      "Gateway to the Suez corridor; the most persistently disrupted chokepoint of the last two years. Diversions around the Cape add 10-14 days to India-bound fertilizer and crude cargo.",
    watchFactors: ["Red Sea shipping attacks", "War-risk insurance zones", "Houthi-linked incident reports"],
  },
  {
    id: "suez",
    name: "Suez Canal / SUMED",
    lat: 30.45,
    lon: 32.35,
    transitVolume: 4.9,
    transitUnit: "mbpd",
    year: 2025,
    source: "EIA World Oil Transit Chokepoints, 1H25 avg.",
    risk: 33,
    trend: -4,
    history: [46, 44, 43, 41, 39, 38, 37, 36, 35, 34, 37, 33],
    summary:
      "Traffic has partly normalised as more carriers accept Cape diversions as the standing routing rather than a temporary detour. Canal Authority toll policy is the softer, slower-moving risk.",
    watchFactors: ["SCA transit toll changes", "Convoy scheduling delays", "Sinai security posture"],
  },
  {
    id: "cape",
    name: "Cape of Good Hope",
    lat: -34.358,
    lon: 18.474,
    transitVolume: 9.1,
    transitUnit: "mbpd",
    year: 2025,
    source: "EIA World Oil Transit Chokepoints, 1H25 avg.",
    risk: 21,
    trend: 1,
    history: [15, 16, 17, 16, 18, 17, 19, 18, 20, 19, 20, 21],
    summary:
      "Absorbing Red Sea diversion traffic; risk here is weather and port-call congestion rather than conflict. A slow-burn indicator of how long Red Sea avoidance persists.",
    watchFactors: ["Agulhas current sea states", "Durban/Cape Town berth queues", "Diversion volume trend"],
  },
];

export const ports: Port[] = [
  { id: "sikka", name: "Sikka", lat: 22.43, lon: 69.83, coast: "west", commodities: ["crude_oil"], routesVia: ["hormuz"] },
  { id: "vadinar", name: "Vadinar", lat: 22.37, lon: 69.72, coast: "west", commodities: ["crude_oil"], routesVia: ["hormuz"] },
  { id: "mundra", name: "Mundra", lat: 22.74, lon: 69.71, coast: "west", commodities: ["crude_oil", "lng", "urea", "dap", "mop"], routesVia: ["hormuz", "bab_el_mandeb", "suez"] },
  { id: "mumbai", name: "Mumbai", lat: 18.95, lon: 72.85, coast: "west", commodities: ["crude_oil"], routesVia: ["hormuz"] },
  { id: "mangalore", name: "New Mangalore", lat: 12.87, lon: 74.84, coast: "west", commodities: ["crude_oil"], routesVia: ["hormuz", "malacca"] },
  { id: "kochi", name: "Kochi", lat: 9.97, lon: 76.24, coast: "west", commodities: ["crude_oil", "lng"], routesVia: ["hormuz", "bab_el_mandeb"] },
  { id: "kandla", name: "Kandla", lat: 23.03, lon: 70.22, coast: "west", commodities: ["urea", "dap", "mop"], routesVia: ["hormuz", "bab_el_mandeb", "cape"] },
  { id: "dahej", name: "Dahej", lat: 21.71, lon: 72.57, coast: "west", commodities: ["lng"], routesVia: ["hormuz"] },
  { id: "hazira", name: "Hazira", lat: 21.12, lon: 72.65, coast: "west", commodities: ["lng"], routesVia: ["hormuz"] },
  { id: "dabhol", name: "Dabhol", lat: 17.54, lon: 73.16, coast: "west", commodities: ["lng"], routesVia: ["hormuz"] },
  { id: "jaigarh", name: "Jaigarh", lat: 17.3, lon: 73.19, coast: "west", commodities: ["lng"], routesVia: ["hormuz"] },
  { id: "paradip", name: "Paradip", lat: 20.26, lon: 86.67, coast: "east", commodities: ["crude_oil", "urea", "dap"], routesVia: ["malacca", "bab_el_mandeb", "cape"] },
  { id: "visakhapatnam", name: "Visakhapatnam", lat: 17.69, lon: 83.3, coast: "east", commodities: ["crude_oil"], routesVia: ["malacca", "hormuz"] },
  { id: "haldia", name: "Haldia", lat: 22.04, lon: 88.06, coast: "east", commodities: ["crude_oil"], routesVia: ["malacca"] },
  { id: "chennai", name: "Chennai", lat: 13.08, lon: 80.29, coast: "east", commodities: ["crude_oil"], routesVia: ["malacca", "hormuz"] },
  { id: "ennore", name: "Ennore", lat: 13.26, lon: 80.34, coast: "east", commodities: ["lng"], routesVia: ["hormuz"] },
  { id: "dhamra", name: "Dhamra", lat: 20.82, lon: 87.0, coast: "east", commodities: ["lng"], routesVia: ["malacca"] },
  { id: "kakinada", name: "Kakinada", lat: 16.98, lon: 82.28, coast: "east", commodities: ["urea", "dap", "mop"], routesVia: ["malacca", "cape"] },
  { id: "krishnapatnam", name: "Krishnapatnam", lat: 14.25, lon: 80.13, coast: "east", commodities: ["urea", "dap", "mop"], routesVia: ["malacca", "cape"] },
];

export const suppliers: Supplier[] = [
  { iso: "IN", name: "India" },
  { iso: "RU", name: "Russia" },
  { iso: "IQ", name: "Iraq" },
  { iso: "SA", name: "Saudi Arabia" },
  { iso: "AE", name: "United Arab Emirates" },
  { iso: "US", name: "United States" },
  { iso: "NG", name: "Nigeria" },
  { iso: "QA", name: "Qatar" },
  { iso: "OM", name: "Oman" },
  { iso: "AU", name: "Australia" },
];

export const newsFeed: NewsItem[] = [
  {
    id: "n1",
    timestamp: "2026-09-14T08:12:00Z",
    headline: "Tanker war-risk premiums for Hormuz transits climb for a third session",
    source: "Lloyd's List",
    chokepointId: "hormuz",
    commodity: "crude_oil",
    sentiment: "elevated",
  },
  {
    id: "n2",
    timestamp: "2026-09-14T07:44:00Z",
    headline: "Red Sea carriers extend Cape of Good Hope routing through Q4",
    source: "TradeWinds",
    chokepointId: "bab_el_mandeb",
    commodity: "lng",
    sentiment: "watch",
  },
  {
    id: "n3",
    timestamp: "2026-09-14T06:58:00Z",
    headline: "Suez Canal Authority holds transit tolls steady for winter schedule",
    source: "Reuters",
    chokepointId: "suez",
    commodity: null,
    sentiment: "routine",
  },
  {
    id: "n4",
    timestamp: "2026-09-14T06:20:00Z",
    headline: "IOCL confirms alternate Iraqi crude cargo after Gulf delay",
    source: "PTI",
    chokepointId: "hormuz",
    commodity: "crude_oil",
    sentiment: "watch",
  },
  {
    id: "n5",
    timestamp: "2026-09-14T05:41:00Z",
    headline: "Durban berth queues lengthen as Cape diversion volumes build",
    source: "Splash247",
    chokepointId: "cape",
    commodity: null,
    sentiment: "watch",
  },
  {
    id: "n6",
    timestamp: "2026-09-14T04:55:00Z",
    headline: "Petronet Dahej reports normal LNG offtake despite Gulf tensions",
    source: "Mint",
    chokepointId: "hormuz",
    commodity: "lng",
    sentiment: "routine",
  },
  {
    id: "n7",
    timestamp: "2026-09-14T03:30:00Z",
    headline: "Singapore Strait traffic advisory issued after collision near Horsburgh",
    source: "MPA Singapore",
    chokepointId: "malacca",
    commodity: null,
    sentiment: "watch",
  },
  {
    id: "n8",
    timestamp: "2026-09-14T02:10:00Z",
    headline: "DAP cargo ex-Jordan reroutes via Cape after Red Sea advisory",
    source: "Fertilizer Week",
    chokepointId: "bab_el_mandeb",
    commodity: "dap",
    sentiment: "elevated",
  },
];

export const lastUpdated = "2026-09-14T08:14:00Z";
