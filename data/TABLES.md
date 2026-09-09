# Tables

Two stores, one set of tables.

**JSON** is what we type and commit. One file per table (or per commodity folder). Nested lists are fine (`"chokepoints": ["hormuz"]`). Git can diff a row.

**SQLite** (`data/flow.db`) is what the graph, CLI, and later MCP query. It is built from the JSON. Do not edit the `.db` by hand. `.gitignore` already ignores `*.db`, so a clone runs a build command and gets a fresh database.

```
JSON seeds  --(src/flow/data loader)-->  data/flow.db  --(queries)-->  graph / CLI
```

Ids are lowercase slugs: `hormuz`, `sikka`, `jamnagar`, `crude_oil`. Same id in JSON and in SQLite.

Every number needs `year`, `source`, and `source_url`. Why we need each table is in [README.md](README.md). This file is the list.

Loaders: `src/flow/data/`. Types: `src/flow/models/`. Graph: `src/flow/graph/` reads the db, not the JSON. News: `src/flow/intel/` writes `data/raw/` and upserts into `events`. Tests: `tests/fixtures/` (tiny JSON, build a temp db in the test).

---

## Index

| Table | JSON (edit this) | SQLite | One row is | In git? |
| --- | --- | --- | --- | --- |
| `commodities` | `data/seeds/commodities.json` | `commodities` | one product we track | JSON yes |
| `suppliers` | `data/seeds/suppliers.json` | `suppliers` | one exporting country | JSON yes |
| `chokepoints` | `data/seeds/chokepoints.json` | `chokepoints` | one strait or canal | JSON yes |
| `ports` | `data/seeds/ports.json` | `ports` | one Indian port | JSON yes |
| `refineries` | `data/seeds/oil/refineries.json` | `refineries` | one Indian refinery | JSON yes |
| `lng_terminals` | `data/seeds/lng/terminals.json` | `lng_terminals` | one Indian LNG terminal | JSON yes |
| `fertilizer_plants` | `data/seeds/fertilizer/plants.json` | `fertilizer_plants` | one Indian plant | JSON yes |
| `imports` | `data/seeds/{oil,lng,fertilizer}/imports.json` | `imports` | one supplier × commodity × year | JSON yes |
| `routes` | `data/seeds/{oil,lng,fertilizer}/routes.json` | `routes` | one cargo path to India | JSON yes |
| `events` | `data/raw/events.jsonl` | `events` | one filtered GDELT article | no |
| `entity_risk` | none | `entity_risk` | live score on a node | no |

JSON arrays become extra SQLite tables (do not stuff a comma-separated string into one column):

| JSON field | SQLite link table |
| --- | --- |
| `ports.commodities[]` | `port_commodities(port_id, commodity_id)` |
| `refineries.grades[]` | `refinery_grades(refinery_id, grade)` |
| `fertilizer_plants.products[]` | `plant_products(plant_id, commodity_id)` |
| `routes.chokepoints[]` | `route_chokepoints(route_id, chokepoint_id)` |
| `events.entities[]` | `event_entities(event_id, entity_id)` |
| `events.commodities[]` | `event_commodities(event_id, commodity_id)` |

`imports` and `routes` are the same JSON shape in oil, LNG, and fertilizer folders. The loader concatenates them into one SQLite table each. Split files so two people can edit without colliding. Fertilizer files mix urea, DAP, and MOP in `commodity`. Do not invent a fourth `imports.json`.

---

## commodities

Lookup. Five rows. No volumes.

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes (`crude_oil`, `lng`, `urea`, `dap`, `mop`) |
| `name` | string | yes |
| `family` | string | yes (`oil`, `gas`, `fertilizer`) |
| `unit` | string | yes (the unit *imports* must use for this id) |

---

## suppliers

| Column | Type | Required |
| --- | --- | --- |
| `iso` | string | yes (ISO 3166-1 alpha-2, `SA`, `QA`, `RU`) |
| `name` | string | yes |
| `lat` | float | no |
| `lon` | float | no |

India (`IN`) can live here as the sink country. Import rows still use the *exporter* iso.

---

## chokepoints

Volumes come from EIA, not from a guess. [World oil transit chokepoints](https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints). Hormuz note: [IEA factsheet (PDF)](https://iea.blob.core.windows.net/assets/c8248eba-8689-46d9-ae4b-b858b59c0f1c/StraitofHormuz2026-Factsheet.pdf).

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes (`hormuz`, `malacca`, `bab_el_mandeb`, `suez`, `cape`) |
| `name` | string | yes |
| `lat` | float | yes |
| `lon` | float | yes |
| `transit_volume` | float | yes |
| `transit_unit` | string | yes (`mbpd` for oil; LNG can be `mtpa` if EIA gives it) |
| `year` | int | yes |
| `source` | string | yes |
| `source_url` | string | yes |

We only need chokepoints that sit on Indian cargoes. Empty rows for Panama are wasted work.

---

## ports

Indian discharge (and a few load ports abroad if you actually use them on a route). IPA: [https://www.ipa.nic.in/](https://www.ipa.nic.in/). Coordinates: [World Port Index](https://msi.nga.mil/Publications/WPI). Ministry: [https://shipmin.gov.in/](https://shipmin.gov.in/).

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes (`sikka`, `mundra`, `dahej`, `paradip`) |
| `name` | string | yes |
| `country_iso` | string | yes (`IN` for Indian ports) |
| `coast` | string | no (`west`, `east`) |
| `lat` | float | yes |
| `lon` | float | yes |
| `commodities` | list of string | yes (ids from `commodities`) |
| `source` | string | yes |
| `source_url` | string | yes |

---

## refineries

PPAC capacity: [https://ppac.gov.in/](https://ppac.gov.in/), [What's new](https://ppac.gov.in/all-whats-new). Company sites if PPAC is missing a plant.

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes |
| `name` | string | yes |
| `operator` | string | yes |
| `lat` | float | yes |
| `lon` | float | yes |
| `capacity` | float | yes |
| `capacity_unit` | string | yes (`mmtpa` or `bpd`, pick one for the whole file) |
| `year` | int | yes |
| `nearest_port` | string | yes (a `ports.id`) |
| `grades` | list of string | no |
| `source` | string | yes |
| `source_url` | string | yes |

---

## lng_terminals

PPAC gas section of the Ready Reckoner. Check the operator if the nameplate is missing. Secondary: [GIIGNL](https://giignl.org/).

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes (`dahej`, `hazira`, ...) |
| `name` | string | yes |
| `operator` | string | yes |
| `lat` | float | yes |
| `lon` | float | yes |
| `capacity_mtpa` | float | yes |
| `year` | int | yes |
| `port` | string | yes (a `ports.id`) |
| `source` | string | yes |
| `source_url` | string | yes |

---

## fertilizer_plants

Enough Indian sinks that the graph is not only ports. DoF: [https://www.fert.nic.in/](https://www.fert.nic.in/). FAI: [https://www.faidelhi.org/](https://www.faidelhi.org/).

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes |
| `name` | string | yes |
| `operator` | string | yes |
| `products` | list of string | yes (`urea`, `dap`, `mop`) |
| `lat` | float | yes |
| `lon` | float | yes |
| `nearest_port` | string | no |
| `source` | string | yes |
| `source_url` | string | yes |

---

## imports

Same columns in `data/seeds/oil/imports.json`, `data/seeds/lng/imports.json`, `data/seeds/fertilizer/imports.json`.

Oil: [PPAC import/export](https://ppac.gov.in/import-export). LNG: same Ready Reckoner, gas tables (crude tables often exclude LNG). Fertilizer: DoF / FAI / [DGFT](https://www.dgft.gov.in/). Cross-check: [Comtrade Plus](https://comtradeplus.un.org/) (HS 2709 crude, 3102.10 urea, 3105.30 DAP, 3104.20 MOP). Prefer the Indian series when they disagree.

| Column | Type | Required |
| --- | --- | --- |
| `commodity` | string | yes |
| `supplier_iso` | string | yes |
| `supplier_name` | string | yes |
| `volume` | float | yes |
| `unit` | string | yes (must match `commodities.unit`) |
| `year` | int | yes |
| `share_of_india_imports` | float | yes (0 to 1) |
| `source` | string | yes |
| `source_url` | string | yes |

Shares for one commodity × year should add to about 1. If you only type the top 8 suppliers, add a leftover row (`supplier_iso: "XX"`, name `Other`) so the total is honest.

```json
{
  "commodity": "crude_oil",
  "supplier_iso": "SA",
  "supplier_name": "Saudi Arabia",
  "volume": 40.2,
  "unit": "mmt",
  "year": 2024,
  "share_of_india_imports": 0.18,
  "source": "PPAC Ready Reckoner, July 2025, table X",
  "source_url": "https://ppac.gov.in/"
}
```

---

## routes

This is the table the cascade walks. One row: this supplier, this commodity, these straits, this Indian port (and optional plant).

Qatar LNG to Dahej lists `hormuz`. US LNG to Dahej does not. Gulf urea lists `hormuz`. Canadian MOP does not. If that difference is only in a comment, the simulator will be wrong.

| Column | Type | Required |
| --- | --- | --- |
| `id` | string | yes |
| `commodity` | string | yes |
| `supplier_iso` | string | yes |
| `chokepoints` | list of string | yes (empty list is allowed) |
| `indian_port` | string | yes |
| `indian_facility` | string | no (refinery / terminal / plant id) |
| `volume` | float | no (if missing, split that supplier's import volume across its routes) |
| `unit` | string | yes if `volume` is set |
| `year` | int | yes |
| `source` | string | yes |
| `source_url` | string | yes |

Files: `data/seeds/oil/routes.json`, `data/seeds/lng/routes.json`, `data/seeds/fertilizer/routes.json`.

---

## events (live)

Not a seed. Script writes `data/raw/` (gitignored). GDELT: [https://www.gdeltproject.org/data.html](https://www.gdeltproject.org/data.html), latest files [lastupdate.txt](http://data.gdeltproject.org/gdeltv2/lastupdate.txt), columns [GKG codebook v2.1 (PDF)](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf).

| Column | Type | Required |
| --- | --- | --- |
| `event_id` | string | yes (`GKGRECORDID` or URL) |
| `observed_at` | string | yes (UTC) |
| `source_name` | string | yes |
| `url` | string | yes |
| `tone` | float | no |
| `entities` | list of string | yes (our ids: `hormuz`, `QA`, `dahej`) |
| `commodities` | list of string | yes |

Dedup on `event_id`. Fetch code belongs in `src/flow/data/` / `src/flow/intel/`, not in `src/flow/graph/`.

---

## entity_risk (derived)

Do not type this. Code scores `events` onto `suppliers` / `chokepoints` / `ports` and stores `live_risk` plus `as_of` on the graph node. Seed volumes do not change.

---

## How they join

```
imports.supplier_iso      -> suppliers.iso
imports.commodity         -> commodities.id
routes.supplier_iso       -> suppliers.iso
route_chokepoints         -> routes.id + chokepoints.id
routes.indian_port        -> ports.id
routes.indian_facility    -> refineries.id or lng_terminals.id or fertilizer_plants.id
refineries.nearest_port   -> ports.id
lng_terminals.port        -> ports.id
event_entities            -> events.event_id + a node id
```

If an id shows up in `routes` and not in the table it points at, the loader should fail. Silent skips make fake cascade numbers.

Query the db, not the JSON:

```python
import sqlite3

conn = sqlite3.connect("data/flow.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    """
    SELECT r.commodity, SUM(i.volume) AS volume
    FROM routes r
    JOIN route_chokepoints rc ON rc.route_id = r.id
    JOIN imports i
      ON i.commodity = r.commodity AND i.supplier_iso = r.supplier_iso AND i.year = r.year
    WHERE rc.chokepoint_id = ?
    GROUP BY r.commodity
    """,
    ("hormuz",),
).fetchall()
```

The command that fills `data/flow.db` will live in `src/flow/data/` (something like `uv run flow data build`). Until that exists, do not create the `.db` by hand.

---

## SQLite sketch

Same columns as the JSON sections above. Primary keys are the ids. Foreign keys on.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE commodities (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  family TEXT NOT NULL,
  unit TEXT NOT NULL
);

CREATE TABLE suppliers (
  iso TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  lat REAL,
  lon REAL
);

CREATE TABLE chokepoints (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  transit_volume REAL NOT NULL,
  transit_unit TEXT NOT NULL,
  year INTEGER NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT NOT NULL
);

CREATE TABLE ports (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  country_iso TEXT NOT NULL,
  coast TEXT,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT NOT NULL
);

CREATE TABLE port_commodities (
  port_id TEXT NOT NULL REFERENCES ports(id),
  commodity_id TEXT NOT NULL REFERENCES commodities(id),
  PRIMARY KEY (port_id, commodity_id)
);

CREATE TABLE routes (
  id TEXT PRIMARY KEY,
  commodity TEXT NOT NULL REFERENCES commodities(id),
  supplier_iso TEXT NOT NULL REFERENCES suppliers(iso),
  indian_port TEXT NOT NULL REFERENCES ports(id),
  indian_facility TEXT,
  volume REAL,
  unit TEXT,
  year INTEGER NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT NOT NULL
);

CREATE TABLE route_chokepoints (
  route_id TEXT NOT NULL REFERENCES routes(id),
  chokepoint_id TEXT NOT NULL REFERENCES chokepoints(id),
  PRIMARY KEY (route_id, chokepoint_id)
);
```

The rest of the `CREATE TABLE` statements follow the column lists above. One SQLite table per JSON table, plus the link tables.
