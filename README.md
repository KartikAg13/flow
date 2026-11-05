# Flow

Multi-agent critical-import resilience for India: crude oil, LNG, and fertilizers.

One chokepoint shock is not one commodity shock. Flow maps suppliers, corridors, and Indian facilities, scores live risk, and simulates the cascade.

GitHub: [https://github.com/KartikAg13/flow](https://github.com/KartikAg13/flow)

---

## First time setup

You need Git, Python 3.12 or newer, and [uv](https://docs.astral.sh/uv/). uv is the package manager. It creates `.venv` and installs whatever is in `pyproject.toml` / `uv.lock`.

### 1. Clone

```bash
git clone https://github.com/KartikAg13/flow.git
cd flow
```

### 2. Install uv

Docs: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen the terminal if `uv` is not found, then check:

```bash
uv --version
```

### 3. Install the project

From the repo root:

```bash
uv sync --group dev
```

That command creates `.venv/`, installs runtime deps plus pytest/ruff, and installs the `flow` CLI into the venv. You do not need to activate the venv if you always prefix commands with `uv run`. Add `--group viz` if you use the notebook.

If `uv sync` complains about the Python version:

```bash
uv python install 3.12
uv sync --group dev
```

### 4. Check that it works

```bash
uv run flow version     # 0.1.0
uv run pytest           # 15 tests
uv run ruff check src tests
```

### 5. Build the database

```bash
uv run flow data build          # data/flow.db from data/seeds (+ any data/raw/events*.jsonl)
uv run flow data gdelt --slices 4   # pull the last hour of GDELT news and score risk
```

`flow.db` is gitignored, so every fresh clone runs `flow data build` once. If your `data/raw/` holds news pulled before the stricter filter (crime and celebrity stories in the feed), run `uv run flow data refilter` once. To keep the news fresh, run the GDELT pull every 15 minutes, for example from cron: `*/15 * * * * cd ~/flow && uv run flow data gdelt`.

### 6. Env file (only for the Copilot)

The AI Copilot calls Groq. Copy `.env.example` to `.env` and put `GROQ_API_KEY` in it (free key: [https://console.groq.com/](https://console.groq.com/)). `.env` is gitignored. Everything else (data, graph, simulation, dashboard) works without a key.

Day to day git: [CONTRIBUTING.md](CONTRIBUTING.md). What data we collect: [data/README.md](data/README.md) and [data/TABLES.md](data/TABLES.md). Plain-language tour: [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

---

## Run it

```bash
cd frontend && npm install && npm run build && cd ..
uv run flow serve               # dashboard + API on http://127.0.0.1:8000
```

While working on the frontend, run `uv run flow serve` and `cd frontend && npm run dev` side by side; Vite (port 5173) proxies `/api` to the Python server.

The CLI gives the same answers without a browser (JSON, so it is easy to check):

```bash
uv run flow risk                          # live 0-100 risk per chokepoint
uv run flow exposure hormuz               # MMT and import share per commodity through a node
uv run flow critical                      # chokepoints and ports India depends on most
uv run flow simulate hormuz --months 6    # closure scenario: losses, facilities, cascade, reserves
uv run flow impact hormuz --months 6      # who it hurts: states, fuel users, farm holdings
uv run flow reroute hormuz --months 6     # ways around: sea detours, bypass pipelines, open entry points
uv run flow ask "What happens if Hormuz is closed for 6 months?"   # multi-agent Copilot
uv run flow mcp world                     # run an MCP server over stdio (also: flow mcp graph)
```

`flow ask` writes the full agent trace (every delegation, tool call and tool result) to `artifacts/trace-*.json`.

---

## Stack

| Piece | Choice |
| --- | --- |
| Package / env | uv, Python ≥ 3.12 |
| Store | SQLite (`data/flow.db`) built from cited JSON seeds, validated with Pydantic |
| News | GDELT 2.0 GKG, 15-minute slices |
| Graph | NetworkX |
| Agents | LangGraph supervisor + two specialists on Groq (`openai/gpt-oss-120b`) |
| Tools | Two MCP servers: `world-model-mcp`, `graph-sim-mcp` |
| API | Python standard library HTTP server |
| Interface | CLI (`flow`) and a React + Leaflet dashboard (`frontend/`) |

---

## Layout

```
src/flow/
  cli.py             every command
  api.py             HTTP API + serves frontend/dist
  models/            Pydantic types for each seed row
  data/              build flow.db, fetch GDELT
  intel/             live chokepoint risk from news
  graph/             NetworkX world model, exposure, critical nodes
  sim/               closure scenarios and the LNG -> urea cascade
  mcp/               world-model-mcp (world.py) and graph-sim-mcp (graph_sim.py)
  agents/            LangGraph supervisor; talks to data only through MCP
data/seeds/          versioned numbers with citations (committed; written by scripts/write_seeds.py)
data/raw/            GDELT extracts (folder stays, files do not)
artifacts/           Copilot traces (folder stays, files do not)
frontend/            dashboard (Vite + React + Leaflet)
tests/
scripts/
notebooks/
```

`data/raw/` and `artifacts/` are empty on purpose after a clone. Git cannot track an empty directory, so each has a `.gitkeep`. Anything you drop in those two folders is ignored by `.gitignore`. Do not commit GDELT extracts or trace JSON.
