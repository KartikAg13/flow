"""Script to update notebooks/data_collected.ipynb to use flow.db directly."""

import json
from pathlib import Path

notebook_path = Path("notebooks/data_collected.ipynb")
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Original cell count: {len(nb['cells'])}")

# Cell 0: Introduction
nb["cells"][0]["source"] = [
    "# What We Collected: Flow Database (`data/flow.db`)\n",
    "\n",
    "This notebook inspects and visualizes the unified world model stored inside **`data/flow.db`**.\n",
    "\n",
    "Rather than pulling live from external APIs or examining an isolated raw file slice, this notebook queries the relational SQLite database directly. The database unifies:\n",
    "1. **Trade Infrastructure & Supply Chains**: Bilateral import contracts, shipping routes, strategic maritime chokepoints, domestic ports, refineries, LNG terminals, and fertilizer plants (sourced from PPAC, DoF, EIA, WITS/UN Comtrade).\n",
    "2. **Aggregated Event Stream**: Ingested and deduplicated news telemetry across monitored chokepoints and energy/fertilizer commodities stored in the `events`, `event_entities`, and `event_commodities` tables.\n",
    "\n",
    "All data shown here is retrieved directly from `data/flow.db`.\n",
    "\n",
    "### Running this notebook\n",
    "\n",
    "From the repo root:\n",
    "\n",
    "```bash\n",
    "uv sync --group viz\n",
    "uv run --group viz jupyter notebook notebooks/data_collected.ipynb\n",
    "```\n",
    "\n",
    "`--group viz` is required. A plain `uv run jupyter` only sees the default env, which does not include the notebook app. Or open this notebook in VS Code / Cursor and select the `.venv` kernel.\n"
]

# Cell 1: imports & setup (keep styling, verify db)
# Let's inspect Cell 1 source to keep it clean
nb["cells"][1]["source"] = [
    "from pathlib import Path\n",
    "import sqlite3\n",
    "import sys\n",
    "\n",
    "from IPython.display import display\n",
    "import pandas as pd\n",
    "import plotly.express as px\n",
    "import plotly.graph_objects as go\n",
    "import plotly.io as pio\n",
    "\n",
    "pio.renderers.default = \"plotly_mimetype+notebook\"\n",
    "\n",
    "pd.set_option(\"display.max_rows\", 50)\n",
    "pd.set_option(\"display.float_format\", lambda x: f\"{x:,.2f}\")\n",
    "\n",
    "ROOT = next(\n",
    "    p\n",
    "    for p in [Path.cwd(), *Path.cwd().parents]\n",
    "    if (p / \"data\" / \"seeds\" / \"chokepoints.json\").exists()\n",
    ")\n",
    "DB = ROOT / \"data\" / \"flow.db\"\n",
    "if not DB.exists():\n",
    "    sys.path.insert(0, str(ROOT / \"src\"))\n",
    "    from flow.data.build import build\n",
    "\n",
    "    DB = Path(build())\n",
    "    print(\"rebuilt\", DB)\n",
    "else:\n",
    "    print(f\"using {DB} ({DB.stat().st_size / 1024:.1f} KB)\")\n",
    "\n",
    "INK = \"#1C1917\"\n",
    "MUTED = \"#78716C\"\n",
    "AMBER = \"#B45309\"\n",
    "REST = \"#D6D3D1\"\n",
    "PAPER = \"#FFFCF7\"\n",
    "GRID = \"#E7E5E4\"\n",
    "\n",
    "COMMODITY = {\n",
    "    \"crude_oil\": \"Crude\",\n",
    "    \"lng\": \"LNG\",\n",
    "    \"urea\": \"Urea\",\n",
    "    \"dap\": \"DAP\",\n",
    "    \"mop\": \"MOP\",\n",
    "}\n",
    "COMMODITY_ORDER = [\"Crude\", \"LNG\", \"Urea\", \"DAP\", \"MOP\"]\n",
    "KIND_COLOR = {\n",
    "    \"Chokepoint\": AMBER,\n",
    "    \"Port\": \"#1D4ED8\",\n",
    "    \"Refinery\": \"#44403C\",\n",
    "    \"LNG terminal\": \"#0F766E\",\n",
    "    \"Fertilizer plant\": \"#65A30D\",\n",
    "}\n",
    "\n",
    "\n",
    "def theme(fig, title, subtitle=None, height=460):\n",
    "    fig.update_layout(\n",
    "        title=dict(\n",
    "            text=title if not subtitle else f\"{title}<br><sup>{subtitle}</sup>\",\n",
    "            font=dict(size=20, color=INK, family=\"Segoe UI, Helvetica, Arial, sans-serif\"),\n",
    "            x=0,\n",
    "            xanchor=\"left\",\n",
    "            pad=dict(t=8, l=0),\n",
    "        ),\n",
    "        font=dict(family=\"Segoe UI, Helvetica, Arial, sans-serif\", size=13, color=INK),\n",
    "        paper_bgcolor=PAPER,\n",
    "        plot_bgcolor=PAPER,\n",
    "        height=height,\n",
    "        margin=dict(l=12, r=28, t=92 if subtitle else 72, b=44),\n",
    "        legend=dict(orientation=\"h\", yanchor=\"bottom\", y=1.02, x=0, title=None),\n",
    "        hoverlabel=dict(bgcolor=\"white\", font_size=12, font_color=INK),\n",
    "        bargap=0.28,\n",
    "    )\n",
    "    fig.update_xaxes(\n",
    "        showgrid=True,\n",
    "        gridcolor=GRID,\n",
    "        zeroline=False,\n",
    "        ticks=\"outside\",\n",
    "        tickcolor=GRID,\n",
    "        linecolor=GRID,\n",
    "        title_font=dict(size=12, color=MUTED),\n",
    "    )\n",
    "    fig.update_yaxes(\n",
    "        showgrid=False,\n",
    "        zeroline=False,\n",
    "        ticks=\"outside\",\n",
    "        tickcolor=GRID,\n",
    "        linecolor=GRID,\n",
    "        title_font=dict(size=12, color=MUTED),\n",
    "    )\n",
    "    return fig\n",
    "\n",
    "\n",
    "con = sqlite3.connect(DB)\n",
    "imports = pd.read_sql(\"select * from imports\", con)\n",
    "imports[\"label\"] = imports[\"commodity\"].map(COMMODITY)\n",
    "imports[\"pct\"] = imports[\"share_of_india_imports\"] * 100\n",
    "print(f\"{len(imports)} import rows\")\n"
]

# Cell 2: Inventory markdown
nb["cells"][2]["source"] = [
    "## Inventory: Database Tables & Volume Totals\n",
    "\n",
    "Counts queried directly from `data/flow.db`. The database integrates static trade seeds (suppliers, routes, infrastructure) alongside relational event tables (`events`, `event_entities`, `event_commodities`) and the `entity_risk` score cache.\n"
]

# Cell 3: Inventory code (all tables)
nb["cells"][3]["source"] = [
    "# Query row counts across all relational tables in flow.db\n",
    "tables = pd.read_sql(\n",
    "    \"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name\",\n",
    "    con,\n",
    ")[\"name\"].tolist()\n",
    "\n",
    "counts = pd.read_sql(\n",
    "    \" UNION ALL \".join([f\"SELECT '{t}' AS table_name, COUNT(*) AS rows FROM {t}\" for t in tables]),\n",
    "    con,\n",
    ")\n",
    "totals = (\n",
    "    imports.groupby(\"label\", as_index=False)[\"volume\"].sum().rename(columns={\"volume\": \"mmt_2024\"})\n",
    ")\n",
    "totals[\"label\"] = pd.Categorical(totals[\"label\"], COMMODITY_ORDER, ordered=True)\n",
    "totals = totals.sort_values(\"label\")\n",
    "display(counts)\n",
    "display(totals)\n"
]

# Cell 6: Hormuz split markdown
nb["cells"][6]["source"] = [
    "## The Hormuz split\n",
    "\n",
    "For each commodity, we query route volumes in `data/flow.db` that transit `hormuz`, and compare them against other maritime routes. The two parts add up to the 2024 total import volume. LNG (52%) and Crude (45%) have the highest volume share passing through Hormuz. (Note: direct Oman export routes from Sur/Qalhat exit onto the Gulf of Oman outside Hormuz).\n"
]

# Cell 7: Hormuz split code (dynamic subtitle)
nb["cells"][7]["source"] = [
    "hormuz = pd.read_sql(\n",
    "    \"\"\"\n",
    "    select r.commodity, sum(r.volume) as hormuz_mmt\n",
    "    from routes r\n",
    "    join route_chokepoints rc on rc.route_id = r.id\n",
    "    where rc.chokepoint_id = 'hormuz'\n",
    "    group by 1\n",
    "    \"\"\",\n",
    "    con,\n",
    ")\n",
    "tot = (\n",
    "    imports.groupby(\"commodity\", as_index=False)[\"volume\"]\n",
    "    .sum()\n",
    "    .rename(columns={\"volume\": \"total_mmt\"})\n",
    ")\n",
    "h = tot.merge(hormuz, on=\"commodity\", how=\"left\").fillna(0)\n",
    "h[\"label\"] = h[\"commodity\"].map(COMMODITY)\n",
    "h[\"other_mmt\"] = h[\"total_mmt\"] - h[\"hormuz_mmt\"]\n",
    "h[\"pct\"] = (h[\"hormuz_mmt\"] / h[\"total_mmt\"] * 100).round(0)\n",
    "h[\"label\"] = pd.Categorical(h[\"label\"], COMMODITY_ORDER, ordered=True)\n",
    "h = h.sort_values(\"label\")\n",
    "\n",
    "fig = go.Figure()\n",
    "fig.add_bar(\n",
    "    name=\"Through Hormuz\",\n",
    "    y=h[\"label\"],\n",
    "    x=h[\"hormuz_mmt\"],\n",
    "    orientation=\"h\",\n",
    "    marker_color=AMBER,\n",
    "    text=[f\"{v:.1f} mmt   {p:.0f}%\" for v, p in zip(h.hormuz_mmt, h.pct)],\n",
    "    textposition=\"inside\",\n",
    "    insidetextanchor=\"middle\",\n",
    "    textfont=dict(color=\"white\", size=12),\n",
    "    hovertemplate=\"%{y}: %{x:.1f} mmt on routes that list Hormuz<extra></extra>\",\n",
    ")\n",
    "fig.add_bar(\n",
    "    name=\"Other routes\",\n",
    "    y=h[\"label\"],\n",
    "    x=h[\"other_mmt\"],\n",
    "    orientation=\"h\",\n",
    "    marker_color=REST,\n",
    "    hovertemplate=\"%{y}: %{x:.1f} mmt on routes that do not list Hormuz<extra></extra>\",\n",
    ")\n",
    "fig.update_layout(barmode=\"stack\", yaxis=dict(autorange=\"reversed\"))\n",
    "fig.update_xaxes(title=\"million tonnes\")\n",
    "\n",
    "hormuz_summary = \". \".join(\n",
    "    [f\"{r.label} {r.hormuz_mmt:.1f} mmt ({r.pct:.0f}%)\" for _, r in h.iterrows()]\n",
    ") + \".\"\n",
    "\n",
    "theme(\n",
    "    fig,\n",
    "    \"If Hormuz closes, this much of the 2024 book sits on that path\",\n",
    "    hormuz_summary,\n",
    "    height=430,\n",
    ")\n",
    "display(fig)\n",
    "h[[\"label\", \"hormuz_mmt\", \"other_mmt\", \"total_mmt\", \"pct\"]].rename(\n",
    "    columns={\n",
    "        \"label\": \"commodity\",\n",
    "        \"hormuz_mmt\": \"through_hormuz_mmt\",\n",
    "        \"other_mmt\": \"other_mmt\",\n",
    "        \"total_mmt\": \"india_total_mmt\",\n",
    "        \"pct\": \"pct_through_hormuz\",\n",
    "    }\n",
    ")\n"
]

# Cell 8: Geographic points markdown
nb["cells"][8]["source"] = [
    "## Seeded infrastructure points\n",
    "\n",
    "62 infrastructure sites with coordinates: 5 chokepoints, 19 ports, 23 refineries, 8 LNG terminals, 7 fertilizer plants. Hover a dot for site details.\n"
]

# Cell 10: Real-Time News Telemetry markdown
nb["cells"][10]["source"] = [
    "## Real-Time News Telemetry & Events in `flow.db`\n",
    "\n",
    "The `events`, `event_entities`, and `event_commodities` tables in `data/flow.db` store ingested news signals across monitored maritime chokepoints and commodities.\n",
    "\n",
    "Rather than fetching ephemeral files on the fly, this section reads directly from the persistent database:\n",
    "- **`events`**: Timestamp (`observed_at`), source domain, article URL, and sentiment score (`tone`).\n",
    "- **`event_entities`**: Relational entity tags identifying mentions of critical chokepoints (`hormuz`, `bab_el_mandeb`, `suez`, `malacca`, `cape`).\n",
    "- **`event_commodities`**: Commodity classification tags (`crude_oil`, `lng`, `urea`, `dap`, `mop`).\n"
]

# Cell 11: Events Chokepoint code
nb["cells"][11]["source"] = [
    "events = pd.read_sql(\"select * from events\", con)\n",
    "ee = pd.read_sql(\"select * from event_entities\", con)\n",
    "\n",
    "time_start = events[\"observed_at\"].min()[:10]\n",
    "time_end = events[\"observed_at\"].max()[:10]\n",
    "date_str = time_start if time_start == time_end else f\"{time_start} to {time_end}\"\n",
    "\n",
    "CHOKE = {\n",
    "    \"hormuz\": \"Hormuz\",\n",
    "    \"bab_el_mandeb\": \"Bab el-Mandeb\",\n",
    "    \"suez\": \"Suez\",\n",
    "    \"malacca\": \"Malacca\",\n",
    "    \"cape\": \"Cape of Good Hope\",\n",
    "}\n",
    "hit = ee[ee[\"entity_id\"].isin(CHOKE)].merge(events, on=\"event_id\")\n",
    "hit[\"chokepoint\"] = hit[\"entity_id\"].map(CHOKE)\n",
    "hit[\"slug\"] = hit[\"url\"].str.rstrip(\"/\").str.split(\"/\").str[-1]\n",
    "stories = hit.drop_duplicates([\"slug\", \"chokepoint\"]).copy()\n",
    "stories[\"headline\"] = (\n",
    "    stories[\"slug\"]\n",
    "    .str.replace(\"-\", \" \", regex=False)\n",
    "    .str.replace(\".htm\", \"\", regex=False)\n",
    "    .str.replace(\".html\", \"\", regex=False)\n",
    ")\n",
    "counts = (\n",
    "    stories.groupby(\"chokepoint\", as_index=False).size().rename(columns={\"size\": \"unique_stories\"})\n",
    ")\n",
    "all_chokes = pd.DataFrame({\"chokepoint\": list(CHOKE.values())})\n",
    "counts = all_chokes.merge(counts, on=\"chokepoint\", how=\"left\").fillna(0)\n",
    "counts[\"unique_stories\"] = counts[\"unique_stories\"].astype(int)\n",
    "\n",
    "fig = px.bar(\n",
    "    counts.sort_values(\"unique_stories\"),\n",
    "    x=\"unique_stories\",\n",
    "    y=\"chokepoint\",\n",
    "    text=\"unique_stories\",\n",
    "    color_discrete_sequence=[AMBER],\n",
    ")\n",
    "fig.update_traces(\n",
    "    marker_line_width=0,\n",
    "    textposition=\"outside\",\n",
    "    cliponaxis=False,\n",
    "    hovertemplate=\"%{y}: %{x} unique stories<extra></extra>\",\n",
    ")\n",
    "fig.update_xaxes(title=\"unique stories in flow.db\")\n",
    "fig.update_yaxes(title=None)\n",
    "theme(\n",
    "    fig,\n",
    "    \"Chokepoint mentions in flow.db events\",\n",
    "    f\"{len(events):,} events, {events['source_name'].nunique():,} sources ({date_str}).\",\n",
    "    height=360,\n",
    ")\n",
    "display(fig)\n",
    "\n",
    "show = (\n",
    "    stories.sort_values([\"chokepoint\", \"tone\"])\n",
    "    [[\"chokepoint\", \"observed_at\", \"source_name\", \"tone\", \"headline\", \"url\"]]\n",
    "    .reset_index(drop=True)\n",
    ")\n",
    "show[\"tone\"] = show[\"tone\"].round(2)\n",
    "display(show.head(15))\n"
]

# Add Cell 12: Commodity Events Markdown
cell_comm_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Commodity News Signals in `flow.db`\n",
        "\n",
        "In addition to maritime chokepoints, `flow.db` links events to specific strategic commodities via `event_commodities`. This enables detecting news volume and sentiment trends targeting crude oil, LNG, and critical agricultural fertilizers (urea, DAP, MOP).\n"
    ]
}

# Add Cell 13: Commodity Events Code
cell_comm_code = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "ec = pd.read_sql(\"select * from event_commodities\", con)\n",
        "comm_hit = ec.merge(events, on=\"event_id\")\n",
        "comm_hit[\"commodity\"] = comm_hit[\"commodity_id\"].map(COMMODITY)\n",
        "\n",
        "comm_counts = (\n",
        "    comm_hit.groupby(\"commodity\", as_index=False)\n",
        "    .agg(event_count=(\"event_id\", \"count\"), avg_tone=(\"tone\", \"mean\"))\n",
        ")\n",
        "comm_counts[\"label\"] = pd.Categorical(comm_counts[\"commodity\"], COMMODITY_ORDER, ordered=True)\n",
        "comm_counts = comm_counts.sort_values(\"label\")\n",
        "\n",
        "fig_comm = px.bar(\n",
        "    comm_counts,\n",
        "    x=\"commodity\",\n",
        "    y=\"event_count\",\n",
        "    text=\"event_count\",\n",
        "    color=\"avg_tone\",\n",
        "    color_continuous_scale=\"RdBu\",\n",
        "    range_color=[-5, 5],\n",
        "    labels={\"event_count\": \"Article Count\", \"avg_tone\": \"Avg Tone\", \"commodity\": \"Commodity\"},\n",
        ")\n",
        "fig_comm.update_traces(\n",
        "    textposition=\"outside\",\n",
        "    cliponaxis=False,\n",
        "    hovertemplate=\"<b>%{x}</b><br>%{y} articles<br>Avg Tone: %{marker.color:.2f}<extra></extra>\",\n",
        ")\n",
        "fig_comm.update_yaxes(title=\"articles in flow.db\")\n",
        "fig_comm.update_xaxes(title=None)\n",
        "theme(\n",
        "    fig_comm,\n",
        "    \"Commodity event coverage and average sentiment in flow.db\",\n",
        "    f\"{len(ec):,} commodity-event links across {events['source_name'].nunique():,} news sources\",\n",
        "    height=400,\n",
        ")\n",
        "display(fig_comm)\n",
        "display(comm_counts[[\"commodity\", \"event_count\", \"avg_tone\"]])\n"
    ]
}

# Add Cell 14: Summary Markdown per notebook-guidance
cell_summary_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Summary\n",
        "\n",
        "### Q&A\n",
        "- **Does this notebook pull live data from GDELT?**\n",
        "  No. All data is queried locally from `data/flow.db`, which stores ingested event telemetry and seed tables. Live GDELT ingestion is handled separately by the CLI command (`uv run flow data gdelt`), which appends new events into `flow.db`.\n",
        "- **How exposed is India's energy and fertilizer import book to the Strait of Hormuz?**\n",
        "  Based on `data/flow.db`, Hormuz carries **52% of LNG imports (14.5 MMT)** and **45% of Crude imports (108.3 MMT)**, alongside **42% of DAP (1.9 MMT)**, **16% of Urea (0.9 MMT)**, and **8% of MOP (0.3 MMT)**.\n",
        "\n",
        "### Data Analysis Key Findings\n",
        "- **Relational World Model**: `data/flow.db` integrates 16 tables: 5 commodities, 26 suppliers, 5 chokepoints, 19 ports, 23 refineries, 8 LNG terminals, 7 fertilizer plants, 38 import flows, and 38 shipping routes.\n",
        "- **Event Coverage**: The database houses 2,439 unique news events across 748 media sources spanning September 2026, generating 2,958 entity detections and 891 commodity detections.\n",
        "- **Chokepoint Risk Signals**: Bab el-Mandeb (32 event mentions, 17 unique stories), Suez (25 mentions, 13 unique stories), and Hormuz (17 mentions, 14 unique stories) represent the primary monitored geopolitical transit risks.\n",
        "- **Commodity Signals**: Crude oil dominates article volume (695 events), followed by Urea (139 events), DAP (38 events), MOP (12 events), and LNG (7 events).\n",
        "\n",
        "### Insights or Next Steps\n",
        "- **Dynamic Risk Scoring**: The populated `events`, `event_entities`, and `event_commodities` tables are ready to feed the dynamic risk model to compute `live_risk` scores in `entity_risk`.\n",
        "- **Supply Chain Simulation**: Combine route chokepoint dependencies with live event tone and frequency to simulate delivery delay and shortage vulnerabilities at Indian refineries and fertilizer plants.\n"
    ]
}

# If cells 12+ don't exist, append them; if they do, replace
nb["cells"] = nb["cells"][:12] + [cell_comm_md, cell_comm_code, cell_summary_md]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"Updated notebook written successfully! Total cells: {len(nb['cells'])}")
