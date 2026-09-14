# Flow — frontend

A standalone instrument-panel UI for the chokepoint risk data described in the
project's `data/seeds/` tables. **This build does not call the Python backend
yet** — everything on screen comes from `src/data/staticData.ts`, a TypeScript
copy of the shape of `chokepoints.json`, `ports.json`, and `suppliers.json`,
plus placeholder news and risk scores.

## Run it

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL. `npm run build` produces a static `dist/` you can
host anywhere; `npm run preview` serves that build locally.

The map uses OpenStreetMap tiles via CARTO's free dark basemap, fetched by
the browser at runtime — you'll need normal internet access for the map
imagery to appear (everything else works offline).

## Layout

```
┌────────────────────────────────────────────────────────────┐
│  FLOW                                          UTC clock    │
├────────────────────────────────────────────────────────────┤
│  live risk shower — one dial per chokepoint, ticks live     │
├───────────────────────────────────────────┬─────────────────┤
│                                            │  current news   │
│               chokepoint map              │  (scrolling,     │
│         (chokepoints, Indian ports,       │   filterable by  │
│          route lines between them)        │   chokepoint)    │
│                                            │                 │
├───────────────────────────────────────────┴─────────────────┤
│  info panel — selected chokepoint detail + fleet stats       │
└────────────────────────────────────────────────────────────┘
```

Clicking a risk dial, a map marker, or a news item all set the same
"selected chokepoint" state and stay in sync.

## File map

```
src/
  data/staticData.ts     mock chokepoints, ports, suppliers, news — swap for API data here
  hooks/useLiveChokepoints.ts   local jitter simulation standing in for a live feed
  utils/risk.ts           risk-band thresholds, colors, time-ago formatting
  components/
    TopBar.tsx
    RiskShower.tsx        top risk dials + sparklines
    MapPanel.tsx           Leaflet map, markers, route lines
    NewsPanel.tsx           news feed
    InfoPanel.tsx           bottom detail panel
    Sparkline.tsx
  App.tsx                 layout + shared selection state
  styles/
    global.css             design tokens (color/type variables)
    app.css                 layout and component styles
```

## Wiring up the real backend later

Everything a real API needs to supply lives in one place:

- Replace the arrays in `src/data/staticData.ts` (`chokepoints`, `ports`,
  `suppliers`, `newsFeed`) with fetch calls — the types (`Chokepoint`, `Port`,
  `NewsItem`, etc.) already match the seed JSON shapes described in
  `data/TABLES.md`, so an endpoint that serializes those SQLite tables
  should drop in with minimal changes.
- `risk`, `trend`, and `history` on `Chokepoint` are currently simulated in
  `useLiveChokepoints.ts`. Swap that hook's `setInterval` jitter for a
  polling or websocket call to the real `entity_risk` table/live score
  endpoint once it exists.
- `newsFeed` items map 1:1 to the `events` table — `chokepointId` and
  `commodity` are meant to come from `event_entities` / `event_commodities`.

No component needs to change shape-wise if the API response matches these
types; only the data-fetching layer does.
