"""Build data/flow.db from data/seeds JSON. Do not edit the db by hand."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pydantic import ValidationError

from flow import models

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE commodities (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, family TEXT NOT NULL, unit TEXT NOT NULL
);
CREATE TABLE suppliers (
  iso TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL, lon REAL
);
CREATE TABLE chokepoints (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
  transit_volume REAL NOT NULL, transit_unit TEXT NOT NULL, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE ports (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, country_iso TEXT NOT NULL, coast TEXT,
  state TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE port_commodities (
  port_id TEXT NOT NULL REFERENCES ports(id),
  commodity_id TEXT NOT NULL REFERENCES commodities(id),
  PRIMARY KEY (port_id, commodity_id)
);
CREATE TABLE refineries (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL, state TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, capacity REAL NOT NULL, capacity_unit TEXT NOT NULL,
  year INTEGER NOT NULL, nearest_port TEXT NOT NULL REFERENCES ports(id),
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE lng_terminals (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL, state TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, capacity_mtpa REAL NOT NULL, year INTEGER NOT NULL,
  port TEXT NOT NULL REFERENCES ports(id), source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE fertilizer_plants (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL, state TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, nearest_port TEXT REFERENCES ports(id),
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE plant_products (
  plant_id TEXT NOT NULL REFERENCES fertilizer_plants(id),
  commodity_id TEXT NOT NULL REFERENCES commodities(id),
  PRIMARY KEY (plant_id, commodity_id)
);
CREATE TABLE imports (
  commodity TEXT NOT NULL REFERENCES commodities(id),
  supplier_iso TEXT NOT NULL REFERENCES suppliers(iso),
  supplier_name TEXT NOT NULL, volume REAL NOT NULL, unit TEXT NOT NULL,
  year INTEGER NOT NULL, share_of_india_imports REAL NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL,
  PRIMARY KEY (commodity, supplier_iso, year)
);
CREATE TABLE routes (
  id TEXT PRIMARY KEY, commodity TEXT NOT NULL REFERENCES commodities(id),
  supplier_iso TEXT NOT NULL REFERENCES suppliers(iso),
  origin TEXT, origin_lat REAL, origin_lon REAL,
  indian_port TEXT NOT NULL REFERENCES ports(id), indian_facility TEXT,
  volume REAL, unit TEXT, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE route_chokepoints (
  route_id TEXT NOT NULL REFERENCES routes(id),
  chokepoint_id TEXT NOT NULL REFERENCES chokepoints(id),
  PRIMARY KEY (route_id, chokepoint_id)
);
CREATE TABLE pipelines (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, fluid TEXT NOT NULL, scope TEXT NOT NULL,
  operator TEXT NOT NULL, supplier_iso TEXT REFERENCES suppliers(iso),
  start_name TEXT, start_lat REAL, start_lon REAL, end_name TEXT, end_lat REAL, end_lon REAL,
  capacity REAL NOT NULL, capacity_unit TEXT NOT NULL, length_km REAL, status TEXT NOT NULL,
  year INTEGER NOT NULL, source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE pipeline_bypasses (
  pipeline_id TEXT NOT NULL REFERENCES pipelines(id),
  chokepoint_id TEXT NOT NULL REFERENCES chokepoints(id),
  PRIMARY KEY (pipeline_id, chokepoint_id)
);
CREATE TABLE pipeline_sites (
  pipeline_id TEXT NOT NULL REFERENCES pipelines(id), node TEXT NOT NULL,
  PRIMARY KEY (pipeline_id, node)
);
CREATE TABLE sea_paths (
  id TEXT PRIMARY KEY, leg TEXT NOT NULL, nm REAL NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE sea_path_chokepoints (
  sea_path_id TEXT NOT NULL REFERENCES sea_paths(id),
  chokepoint_id TEXT NOT NULL REFERENCES chokepoints(id),
  PRIMARY KEY (sea_path_id, chokepoint_id)
);
CREATE TABLE events (
  event_id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, source_name TEXT NOT NULL,
  url TEXT NOT NULL, tone REAL
);
CREATE TABLE event_entities (
  event_id TEXT NOT NULL REFERENCES events(event_id), entity_id TEXT NOT NULL,
  PRIMARY KEY (event_id, entity_id)
);
CREATE TABLE event_commodities (
  event_id TEXT NOT NULL REFERENCES events(event_id),
  commodity_id TEXT NOT NULL REFERENCES commodities(id),
  PRIMARY KEY (event_id, commodity_id)
);
CREATE TABLE entity_risk (
  entity_id TEXT PRIMARY KEY, live_risk REAL NOT NULL, as_of TEXT NOT NULL
);
CREATE TABLE spr_sites (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, state TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, capacity_mmt REAL NOT NULL, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE state_stats (
  state TEXT NOT NULL, metric TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL,
  year INTEGER NOT NULL, source TEXT NOT NULL, source_url TEXT NOT NULL,
  PRIMARY KEY (state, metric)
);
CREATE TABLE fuel_segments (
  fuel TEXT NOT NULL, segment TEXT NOT NULL, share REAL NOT NULL, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL, PRIMARY KEY (fuel, segment)
);
CREATE TABLE factors (
  id TEXT PRIMARY KEY, value REAL NOT NULL, unit TEXT NOT NULL, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
"""

COMMODITY_IDS = {"crude_oil", "lng", "urea", "dap", "mop"}
FOLDERS = ("oil", "lng", "fertilizer")

# table, row model, seed files. Order matters: foreign keys point up the list.
TABLES = [
    ("commodities", models.Commodity, ["commodities.json"]),
    ("suppliers", models.Supplier, ["suppliers.json"]),
    ("chokepoints", models.Chokepoint, ["chokepoints.json"]),
    ("ports", models.Port, ["ports.json"]),
    ("refineries", models.Refinery, ["oil/refineries.json"]),
    ("lng_terminals", models.LngTerminal, ["lng/terminals.json"]),
    ("fertilizer_plants", models.FertilizerPlant, ["fertilizer/plants.json"]),
    ("spr_sites", models.SprSite, ["oil/spr.json"]),
    ("factors", models.Factor, ["factors.json"]),
    ("state_stats", models.StateStat, ["states.json"]),
    ("fuel_segments", models.FuelSegment, ["segments.json"]),
    ("imports", models.Import, [f"{f}/imports.json" for f in FOLDERS]),
    ("routes", models.Route, [f"{f}/routes.json" for f in FOLDERS]),
    ("pipelines", models.Pipeline, ["pipelines.json"]),
    ("sea_paths", models.SeaPath, ["sea_paths.json"]),
]
# JSON list field -> link table (row id, list item)
LINKS = {
    "commodities": "port_commodities",
    "products": "plant_products",
    "chokepoints": "route_chokepoints",
    "bypasses": "pipeline_bypasses",
    "sites": "pipeline_sites",
    "passes": "sea_path_chokepoints",
}
# pipeline site "kind:id" -> table holding that id
SITE_TABLES = {"port": "ports", "refinery": "refineries", "lng_terminal": "lng_terminals"}
SITE_TABLES |= {"fertilizer_plant": "fertilizer_plants"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_db() -> Path:
    return repo_root() / "data" / "flow.db"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open flow.db with dict-like rows, building it from the seeds on first use."""
    db_path = db_path or default_db()
    if not db_path.exists():
        build(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def _executemany(conn: sqlite3.Connection, sql: str, rows: list) -> None:
    if rows:
        conn.executemany(sql, rows)


def _insert_seeds(conn: sqlite3.Connection, seeds: Path) -> None:
    for table, model, files in TABLES:
        for name in files:
            for raw in _load(seeds / name):
                try:
                    row = model.model_validate(raw).model_dump()
                except ValidationError as e:
                    raise ValueError(f"data/seeds/{name}: {e}") from None
                links = {k: row.pop(k) for k in list(row) if k in LINKS}
                cols = ", ".join(row)
                marks = ", ".join("?" * len(row))
                conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(row.values()))
                for field, items in links.items():
                    sql = f"INSERT INTO {LINKS[field]} VALUES (?,?)"
                    _executemany(conn, sql, [(row["id"], x) for x in items])


def build(db_path: Path | None = None) -> Path:
    root = repo_root()
    db_path = db_path or default_db()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        _insert_seeds(conn, root / "data" / "seeds")
        # indian_facility can point at three tables, so no FK covers it; silent skips fake numbers
        orphans = conn.execute(
            """SELECT id, indian_facility FROM routes WHERE indian_facility NOT IN
               (SELECT id FROM refineries UNION SELECT id FROM lng_terminals
                UNION SELECT id FROM fertilizer_plants)"""
        ).fetchall()
        if orphans:
            raise ValueError(f"routes point at unknown facilities: {orphans}")
        for pid, node in conn.execute("SELECT pipeline_id, node FROM pipeline_sites").fetchall():
            kind, _, key = node.partition(":")
            table = SITE_TABLES.get(kind)
            found = table and conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (key,)).fetchone()
            if not found:
                raise ValueError(f"pipeline {pid} links an unknown site: {node}")
        conn.commit()
    finally:
        conn.close()

    for events_file in sorted((root / "data" / "raw").glob("events*.jsonl")):
        append_events(events_file, db_path)
    return db_path


def append_events(
    events: list[dict] | Path | str,
    db_path: Path | None = None,
) -> int:
    """Incrementally append events to flow.db without rebuilding the database.

    Accepts either a list of event dictionaries or a path to a JSONL file.
    Uses INSERT OR IGNORE on events, event_entities, and event_commodities
    to safely skip duplicates while preserving historical events and all seed tables.

    Returns:
        int: Number of new events inserted into the events table.
    """
    db_path = db_path or default_db()
    if not db_path.exists():
        build(db_path)

    event_list: list[dict] = []
    if isinstance(events, (str, Path)):
        p = Path(events)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        event_list.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    elif isinstance(events, list):
        event_list = events

    if not event_list:
        return 0

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        event_rows, ent_rows, comm_rows = [], [], []
        seen: set[str] = set()
        for e in event_list:
            eid = e.get("event_id")
            if not eid or eid in seen:
                continue
            seen.add(eid)
            event_rows.append((eid, e["observed_at"], e["source_name"], e["url"], e.get("tone")))
            for ent in e.get("entities") or []:
                ent_rows.append((eid, ent))
            for comm in e.get("commodities") or []:
                if comm in COMMODITY_IDS:
                    comm_rows.append((eid, comm))

        cur.execute("SELECT COUNT(*) FROM events")
        before_count = cur.fetchone()[0]

        _executemany(conn, "INSERT OR IGNORE INTO events VALUES (?,?,?,?,?)", event_rows)
        _executemany(conn, "INSERT OR IGNORE INTO event_entities VALUES (?,?)", ent_rows)
        _executemany(conn, "INSERT OR IGNORE INTO event_commodities VALUES (?,?)", comm_rows)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM events")
        after_count = cur.fetchone()[0]
        return after_count - before_count
    finally:
        conn.close()
