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

That command creates `.venv/`, installs runtime deps plus pytest/ruff, and installs the `flow` CLI into the venv. You do not need to activate the venv if you always prefix commands with `uv run`.

If `uv sync` complains about the Python version:

```bash
uv python install 3.12
uv sync --group dev
```

### 4. Check that it works

```bash
uv run flow version
uv run pytest
```

`flow version` should print `0.1.0`. pytest may collect zero tests until we write some. That is fine.

### 5. Env file (later)

Groq is not needed for the first data and graph work. When agents land, copy `.env.example` to `.env` and put `GROQ_API_KEY` in it. `.env` is gitignored. Get a key from [https://console.groq.com/](https://console.groq.com/).

Day to day git: [CONTRIBUTING.md](CONTRIBUTING.md). What data we collect: [data/README.md](data/README.md).

---

## Stack for backend

| Piece | Choice |
| --- | --- |
| Package / env | uv, Python ≥ 3.12 |
| Agents | LangGraph + Groq |
| Tools | MCP servers |
| Graph | NetworkX |
| Events | GDELT + Chroma |
| Interface | CLI (`flow`) |

Frontend framework is not decided.

---

## Layout

```
src/flow/            Python package (uv run flow)
  cli.py
  models/
  data/              loaders
  graph/
  intel/
  sim/
  mcp/
  agents/
data/seeds/          versioned numbers with citations (committed)
data/raw/            GDELT zips and extracts (folder stays, files do not)
artifacts/           local traces and demo output (folder stays, files do not)
tests/
scripts/
notebooks/
```

`data/raw/` and `artifacts/` are empty on purpose after a clone. Git cannot track an empty directory, so each has a `.gitkeep`. Anything you drop in those two folders is ignored by `.gitignore`. Do not commit GDELT zips or trace JSON.
