"""world-model-mcp: read-only tools over flow.db (live risk, news, import mix, SQL)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from mcp.server.mcpserver import MCPServer

from flow import intel
from flow.data.build import connect, default_db

mcp = MCPServer(
    "world-model-mcp",
    instructions="Read-only facts about India's crude oil, LNG, urea, DAP and MOP imports: "
    "suppliers, chokepoints, Indian ports and facilities, GDELT news and live risk scores.",
)


@mcp.tool()
def risk_scores() -> list[dict]:
    """Live 0-100 news risk per chokepoint (GDELT mention volume and negative tone, 24 h
    half-life). 0-34 nominal, 35-59 watch, 60+ elevated."""
    with closing(connect()) as con:
        as_of = con.execute("SELECT max(observed_at) FROM events").fetchone()[0]
        names = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM chokepoints")}
        return [
            {"id": k, "name": names[k], "risk": v, "as_of": as_of}
            for k, v in sorted(intel.scores(con).items(), key=lambda kv: -kv[1])
        ]


@mcp.tool()
def recent_events(entity_id: str, limit: int = 8) -> list[dict]:
    """Latest GDELT articles that mention an entity: a chokepoint id (hormuz, bab_el_mandeb, suez,
    malacca, cape), a supplier ISO code (QA, SA, RU, ...) or an Indian port id. Tone < 0 is
    negative coverage."""
    with closing(connect()) as con:
        rows = con.execute(
            """SELECT e.observed_at, e.source_name, e.url, round(e.tone, 1) AS tone
               FROM events e JOIN event_entities ee USING (event_id)
               WHERE ee.entity_id = ? ORDER BY e.observed_at DESC LIMIT ?""",
            (entity_id, min(limit, 25)),
        )
        return [dict(r) for r in rows]


@mcp.tool()
def import_mix(commodity: str) -> list[dict]:
    """India's suppliers of one commodity (crude_oil, lng, urea, dap, mop): volume in MMT, share
    of imports, year and source."""
    with closing(connect()) as con:
        rows = con.execute(
            """SELECT supplier_name, volume AS mmt, share_of_india_imports AS share, year, source
               FROM imports WHERE commodity = ? ORDER BY volume DESC""",
            (commodity,),
        )
        return [dict(r) for r in rows]


@mcp.tool()
def query(sql: str) -> list[dict]:
    """Run one read-only SQL SELECT on flow.db (at most 50 rows). Tables: commodities, suppliers,
    chokepoints, ports, port_commodities, refineries, lng_terminals, fertilizer_plants,
    plant_products, spr_sites, factors, imports, routes, route_chokepoints, events,
    event_entities, event_commodities, entity_risk."""
    connect().close()  # builds flow.db on first use
    with closing(sqlite3.connect(f"file:{default_db()}?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql).fetchmany(50)]


if __name__ == "__main__":
    mcp.run("stdio")
