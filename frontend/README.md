# Flow — dashboard

The dashboard for Flow's live chokepoint risk, import corridors, news and closure scenarios. All data comes from the Python API (`src/flow/api.py`); nothing on screen is mocked.

## Run it

Production-style, one process:

```bash
cd frontend && npm install && npm run build
cd .. && uv run flow serve        # http://127.0.0.1:8000
```

While editing the UI, run both:

```bash
uv run flow serve                 # API on :8000
cd frontend && npm run dev        # http://localhost:5173, proxies /api to :8000
```

`npm install` must finish without `ERESOLVE`. If npm blocks esbuild's install script (npm 12 does this by default), run this once, then `npm run dev` again:

```bash
npm install-scripts approve esbuild
npm rebuild esbuild
```

The map uses Esri's light and dark gray canvas tiles, fetched by the browser at runtime, so it needs internet access for the map imagery. Everything else works offline.

## Layout

- **Top bar:** freshness of the GDELT data, and the **Ask Copilot** button.
- **Risk row:** one card per chokepoint. Each card shows the live 0–100 score, its band (Nominal, Watch, Elevated), the change since the previous GDELT slice, and a sparkline on a fixed 0–100 scale.
- **Map:** chokepoints, Indian ports, refineries, terminals, plants and strategic reserves. Lanes run from each chokepoint to the ports its cargo reaches, coloured by risk, with line width showing tonnes per year.
- **News:** GDELT articles about the selected chokepoint (or all), with tone and tags.
- **Details:** India's import share through the selected chokepoint, and **Simulate closure** for 1, 3, 6 or 12 months.
- **Copilot sheet:** the deterministic closure scenario, plus questions to the multi-agent Copilot (needs `GROQ_API_KEY`).

Clicking a risk card, a map marker, a lane or a news tag selects that chokepoint everywhere.

## Files

```
src/
  api.ts                     typed client for /api/* (shapes match src/flow/api.py)
  hooks/usePoll.ts           polling with last-good-data, and the light/dark hook
  utils/risk.ts              risk bands and number formatting
  components/                TopBar, RiskShower, Sparkline, MapPanel, NewsPanel, InfoPanel, CopilotSheet
  styles/global.css          tokens (Apple system colours, light + dark), base, accessibility
  styles/app.css             layout and components
```

## Design notes

The design follows Apple's interface guidelines:

- system font with size-specific tracking
- light and dark system colours
- a translucent top bar and Copilot sheet over solid content cards
- press feedback on pointer-down
- a sheet that leaves and returns along the same edge as its trigger, and becomes a bottom sheet on phones

It also respects `prefers-reduced-motion` (cross-fade instead of a slide), `prefers-reduced-transparency` (solid materials) and `prefers-contrast: more`.
