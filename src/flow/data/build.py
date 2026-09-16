"""Build data/flow.db from data/seeds JSON. Do not edit the db by hand."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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
  lat REAL NOT NULL, lon REAL NOT NULL, source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE port_commodities (
  port_id TEXT NOT NULL REFERENCES ports(id),
  commodity_id TEXT NOT NULL REFERENCES commodities(id),
  PRIMARY KEY (port_id, commodity_id)
);
CREATE TABLE refineries (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, capacity REAL NOT NULL, capacity_unit TEXT NOT NULL,
  year INTEGER NOT NULL, nearest_port TEXT NOT NULL REFERENCES ports(id),
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE lng_terminals (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL, capacity_mtpa REAL NOT NULL, year INTEGER NOT NULL,
  port TEXT NOT NULL REFERENCES ports(id), source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE fertilizer_plants (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, operator TEXT NOT NULL,
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
  indian_port TEXT NOT NULL REFERENCES ports(id), indian_facility TEXT,
  volume REAL, unit TEXT, year INTEGER NOT NULL,
  source TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE route_chokepoints (
  route_id TEXT NOT NULL REFERENCES routes(id),
  chokepoint_id TEXT NOT NULL REFERENCES chokepoints(id),
  PRIMARY KEY (route_id, chokepoint_id)
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
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def _executemany(conn: sqlite3.Connection, sql: str, rows: list) -> None:
    if rows:
        conn.executemany(sql, rows)


def build(db_path: Path | None = None) -> Path:
    root = repo_root()
    seeds = root / "data" / "seeds"
    db_path = db_path or (root / "data" / "flow.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)

        _executemany(
            conn,
            "INSERT INTO commodities VALUES (?,?,?,?)",
            [
                (r["id"], r["name"], r["family"], r["unit"])
                for r in _load(seeds / "commodities.json")
            ],
        )
        _executemany(
            conn,
            "INSERT INTO suppliers VALUES (?,?,?,?)",
            [
                (r["iso"], r["name"], r.get("lat"), r.get("lon"))
                for r in _load(seeds / "suppliers.json")
            ],
        )
        _executemany(
            conn,
            "INSERT INTO chokepoints VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["name"],
                    r["lat"],
                    r["lon"],
                    r["transit_volume"],
                    r["transit_unit"],
                    r["year"],
                    r["source"],
                    r["source_url"],
                )
                for r in _load(seeds / "chokepoints.json")
            ],
        )

        ports = _load(seeds / "ports.json")
        _executemany(
            conn,
            "INSERT INTO ports VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["name"],
                    r["country_iso"],
                    r.get("coast"),
                    r["lat"],
                    r["lon"],
                    r["source"],
                    r["source_url"],
                )
                for r in ports
            ],
        )
        _executemany(
            conn,
            "INSERT INTO port_commodities VALUES (?,?)",
            [(r["id"], c) for r in ports for c in r.get("commodities", [])],
        )

        _executemany(
            conn,
            "INSERT INTO refineries VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["name"],
                    r["operator"],
                    r["lat"],
                    r["lon"],
                    r["capacity"],
                    r["capacity_unit"],
                    r["year"],
                    r["nearest_port"],
                    r["source"],
                    r["source_url"],
                )
                for r in _load(seeds / "oil" / "refineries.json")
            ],
        )
        _executemany(
            conn,
            "INSERT INTO lng_terminals VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["name"],
                    r["operator"],
                    r["lat"],
                    r["lon"],
                    r["capacity_mtpa"],
                    r["year"],
                    r["port"],
                    r["source"],
                    r["source_url"],
                )
                for r in _load(seeds / "lng" / "terminals.json")
            ],
        )

        plants = _load(seeds / "fertilizer" / "plants.json")
        _executemany(
            conn,
            "INSERT INTO fertilizer_plants VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["name"],
                    r["operator"],
                    r["lat"],
                    r["lon"],
                    r.get("nearest_port"),
                    r["source"],
                    r["source_url"],
                )
                for r in plants
            ],
        )
        _executemany(
            conn,
            "INSERT INTO plant_products VALUES (?,?)",
            [(r["id"], c) for r in plants for c in r.get("products", [])],
        )

        import_rows = []
        route_rows = []
        route_chokes = []
        for folder in ("oil", "lng", "fertilizer"):
            import_rows.extend(_load(seeds / folder / "imports.json"))
            for r in _load(seeds / folder / "routes.json"):
                route_rows.append(r)
                for choke in r.get("chokepoints") or []:
                    route_chokes.append((r["id"], choke))

        _executemany(
            conn,
            "INSERT INTO imports VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    r["commodity"],
                    r["supplier_iso"],
                    r["supplier_name"],
                    r["volume"],
                    r["unit"],
                    r["year"],
                    r["share_of_india_imports"],
                    r["source"],
                    r["source_url"],
                )
                for r in import_rows
            ],
        )
        _executemany(
            conn,
            "INSERT INTO routes VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["commodity"],
                    r["supplier_iso"],
                    r["indian_port"],
                    r.get("indian_facility"),
                    r.get("volume"),
                    r.get("unit"),
                    r["year"],
                    r["source"],
                    r["source_url"],
                )
                for r in route_rows
            ],
        )
        _executemany(conn, "INSERT INTO route_chokepoints VALUES (?,?)", route_chokes)

        raw_dir = root / "data" / "raw"
        event_files = sorted(raw_dir.glob("events*.jsonl")) if raw_dir.exists() else []
        if event_files:
            events, ents, comms = [], [], []
            seen: set[str] = set()
            for ef in event_files:
                for line in ef.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if e["event_id"] in seen:
                        continue
                    seen.add(e["event_id"])
                    events.append(
                        (e["event_id"], e["observed_at"], e["source_name"], e["url"], e.get("tone"))
                    )
                    ents.extend((e["event_id"], x) for x in e.get("entities") or [])
                    comms.extend(
                        (e["event_id"], x)
                        for x in e.get("commodities") or []
                        if x in {"crude_oil", "lng", "urea", "dap", "mop"}
                    )
            _executemany(conn, "INSERT OR IGNORE INTO events VALUES (?,?,?,?,?)", events)
            _executemany(conn, "INSERT OR IGNORE INTO event_entities VALUES (?,?)", ents)
            _executemany(conn, "INSERT OR IGNORE INTO event_commodities VALUES (?,?)", comms)

        conn.commit()
    finally:
        conn.close()
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
    root = repo_root()
    db_path = db_path or (root / "data" / "flow.db")
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
                if comm in {"crude_oil", "lng", "urea", "dap", "mop"}:
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
