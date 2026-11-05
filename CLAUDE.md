# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Flow models India's critical imports: crude oil, LNG, and fertilizers (urea, DAP, MOP are three separate commodities). It maps suppliers, the chokepoints their cargo passes, and Indian ports and facilities. It scores live chokepoint risk from GDELT news, simulates closures (including the LNG → urea cascade), and answers questions through a LangGraph multi-agent Copilot that reaches data only via two MCP servers. It is a two-person college major project; `docs/` (gitignored) holds the synopsis it is graded against.

## Commands

Backend (Python ≥ 3.12, managed with uv; always prefix commands with `uv run`):

```bash
uv sync --group dev                 # runtime (incl. langgraph, langchain-groq, mcp) + pytest/ruff; add --group viz for the notebook
uv run pytest                       # all tests (~3 s; the agent test spawns both MCP servers over stdio)
uv run pytest tests/test_graph_sim.py::test_six_month_hormuz_closure   # single test
uv run ruff check src tests scripts && uv run ruff format src tests scripts

uv run flow data build              # rebuild data/flow.db from seeds + data/raw/events*.jsonl, then rescore risk
uv run flow data gdelt --slices 4   # fetch latest GDELT GKG slices -> data/raw/events-<stamp>.jsonl, append, rescore
uv run flow data ingest [-f FILE]   # append a JSONL of events without rebuilding
uv run flow data refilter           # re-download every slice in data/raw, re-apply the news filter, rebuild
uv run flow risk | exposure hormuz | critical | simulate hormuz --months 6 | impact hormuz | reroute hormuz   # deterministic JSON
uv run flow ask "..."               # Copilot; needs GROQ_API_KEY in .env; trace -> artifacts/trace-*.json
uv run flow serve                   # API + built dashboard on 127.0.0.1:8000
uv run flow mcp world | graph       # run an MCP server over stdio
uv run python scripts/write_seeds.py   # regenerate most data/seeds/*.json (see below); sea paths need searoute (dev group)
```

Frontend (`frontend/`, Vite + React 18 + TypeScript + react-leaflet), run from `frontend/`:

```bash
npm install && npm run dev          # :5173, proxies /api to :8000 (run `uv run flow serve` too)
npm run build                       # tsc -b && vite build -> dist/, which `flow serve` serves
```

If npm blocks esbuild's install script, run `npm install-scripts approve esbuild && npm rebuild esbuild`. The frontend has no lint or test scripts; `npm run build` is the type check.

## Architecture

Data flows one way: **JSON seeds → SQLite → graph/intel → sim → MCP → agents**, with the API and CLI as direct consumers.

- **Seeds** (`data/seeds/**/*.json`, committed) are the source of truth. Every numeric row carries `year`, `source`, `source_url`. Ids are lowercase slugs; suppliers use ISO-2 codes. `scripts/write_seeds.py` writes every seed file except `commodities.json` and `chokepoints.json` (hand-written). If you edit a generated JSON file directly, also update the script, or the next run overwrites it.
- **`data/build.py`** holds the whole SQLite schema (`SCHEMA`) and a table list (`TABLES`: table, Pydantic model, seed files, in FK order). `build()` validates each row with `flow.models` (extra keys fail), inserts by column name, explodes list fields into link tables via `LINKS`, rejects routes whose `indian_facility` is unknown, then replays `data/raw/events*.jsonl` through `append_events()` (`INSERT OR IGNORE`, idempotent). `connect()` opens `flow.db` with `sqlite3.Row` and builds it on first use. **`build()` deletes the db first**, so events ingested from a file outside `data/raw/` are lost on rebuild; keep every events file in `data/raw/`.
- **`data/gdelt.py`** prefilters GKG rows by commodity themes/keywords, then keeps a row only if it names a commodity or a chokepoint/port; a country name alone is not enough. All matching uses word boundaries (substrings turned "bureau" into urea). `ENV_OIL`/`ENV_GAS` themes count only with "oil"/"gas" in the URL or names. Aliases in `ENTITY_ALIASES` must match seed ids. After changing the filter, run `flow data refilter` so stored news follows it.
- **`intel/`** scores the five chokepoints 0–100: per-event weight `(1 + max(0, -tone)/5)` with a 24 h half-life, over a 72 h window, divided by the number of distinct slices, squashed with `K`, a calibration constant. `scores()` is pure; `store()` writes `entity_risk`; `history()` gives sparkline points.
- **`graph/`** builds a NetworkX DiGraph from the db (never JSON). Node ids are `kind:id` (`port:dahej` and `lng_terminal:dahej` both exist). Each route adds supplier → chokepoints → port → facility, and every node on the path lists the route ids that cross it. `exposure()` sums those routes. `G.graph` carries `routes`, `factors` and `spr`, so the graph is the whole in-memory world model. `resolve()` accepts bare ids.
- **`sim/`** `close(G, chokepoints, months)`: blocked routes = routes on the closed chokepoint nodes (no detours, a stated assumption), prorated by months. Cascade = lost LNG × `fertilizer_gas_share` × `lng_gcal_per_t` / `urea_gcal_per_t`, all from `factors.json`. It also reports SPR days of cover and unaffected suppliers. `impact()` takes the same arguments and says where the loss lands (states of the ports and plants on blocked routes, plus urea output at risk by producing state) and who runs short: crude net of the SPR × refinery yield − exports stopped, and fertilizer imports + cascade, each spread pro rata over state sales, PPAC fuel user segments and Agriculture Census farm holdings (`state_stats`, `fuel_segments`). `reroute()` suggests ways around: the shortest precomputed sea path (`sea_paths`) that avoids the closed chokepoints, with the extra sailing days at 14 knots eating into what arrives; India's share of EIA's spare Hormuz bypass pipeline capacity (Saudi East-West, UAE ADCOP), pro rata to its share of Hormuz crude; cargo with no way around; and open import points with domestic `pipelines` inland. `close()` also lists `downstream`: inland sites fed by pipeline from an import point that lost cargo.
- **`mcp/`**: `world.py` (risk_scores, recent_events, import_mix, read-only `query` via `mode=ro`) and `graph_sim.py` (exposure, critical_nodes, simulate_closure, closure_impact, reroute_options). They use MCP 2.0's `MCPServer`; result fields are snake_case (`is_error`, `input_schema`).
- **`agents/`** never imports graph/sim/data. The supervisor LLM gets handoff tools `ask_risk_analyst` / `ask_sim_analyst`; the `team` node runs each specialist's tool loop against its own MCP server (spawned with `sys.executable -m flow.mcp.<module>` over stdio). The specialist's report returns as the handoff's ToolMessage. Traces go to `artifacts/`. `ask(question, llm=..., trace_dir=...)` accepts any tool-calling chat model; tests use a scripted fake.
- **`api.py`** (stdlib `ThreadingHTTPServer`) serves `/api/dashboard`, `/api/news`, `/api/sim` and `POST /api/ask`, and serves `frontend/dist` as static files. News headlines are rebuilt from URL slugs (GKG has none) and deduplicated.
- **Frontend**: `src/api.ts` mirrors the API payloads. `usePoll` refreshes every 60 s. Risk colours are CSS variables keyed off `--band`. Leaflet path classes must be passed as the `className` prop (not `pathOptions`) and be part of the React `key`, because Leaflet only applies className on creation. Map tiles are Esri gray canvas (CARTO now needs a key).

Domain rule: the chokepoint list on each route must be right, because the cascade depends on it. `write_seeds.py` checks it: each route's chokepoints must match a real sea path from its export terminal (this caught Mozambique LNG and Canadian potash wrongly marked "via Cape"). For example, Qatari LNG to west-coast terminals passes Hormuz but Omani LNG and urea (shipped from Sur/Qalhat, outside the strait) do not. Put this on the route row, not in a comment.

## Conventions

- Tests build a temporary db with `build(tmp_path / "flow.db")` (it still replays the repo's `data/raw` events) and never download GDELT. MCP tools can be tested in-process with `mcp.Client(server)`.
- Git workflow (see CONTRIBUTING.md): no PRs. Work on a branch named `phase-<n>/<nn>-<slug>`, merge `main` into it, run pytest and ruff, then merge into `main` and push.
- Do not commit `.env`, `data/raw/*`, `artifacts/*`, `*.db`, or `docs/`. `.env` holds `GROQ_API_KEY` (see `.env.example`); only the Copilot needs it.
