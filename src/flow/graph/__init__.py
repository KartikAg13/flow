"""NetworkX world model, built from flow.db (never from the JSON, never downloads news).

Nodes are "kind:id" (supplier:QA, chokepoint:hormuz, port:dahej, refinery:koyali, ...). Each route
adds the path supplier -> chokepoints -> Indian port -> facility, and every node on the path lists
the route ids that cross it. LNG terminals feed urea plants through one pooled "gas_grid" node.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import networkx as nx

from flow.data.build import connect

NODE_TABLES = [
    ("suppliers", "supplier", "iso"),
    ("chokepoints", "chokepoint", "id"),
    ("ports", "port", "id"),
    ("refineries", "refinery", "id"),
    ("lng_terminals", "lng_terminal", "id"),
    ("fertilizer_plants", "fertilizer_plant", "id"),
]
FACILITY_KIND = {"crude_oil": "refinery", "lng": "lng_terminal"}  # fertilizer routes end at a port


def build_graph(db_path: Path | None = None) -> nx.DiGraph:
    con = connect(db_path)
    try:
        G = nx.DiGraph()
        for table, kind, key in NODE_TABLES:
            for row in con.execute(f"SELECT * FROM {table}"):
                G.add_node(f"{kind}:{row[key]}", kind=kind, routes=[], **dict(row))

        routes = {}
        for row in con.execute("SELECT * FROM routes ORDER BY volume DESC"):
            r = dict(row)
            r["chokepoints"] = [
                c
                for (c,) in con.execute(
                    "SELECT chokepoint_id FROM route_chokepoints WHERE route_id = ? ORDER BY rowid",
                    (r["id"],),
                )
            ]
            path = [f"supplier:{r['supplier_iso']}", *(f"chokepoint:{c}" for c in r["chokepoints"])]
            path.append(f"port:{r['indian_port']}")
            if r["indian_facility"]:
                path.append(f"{FACILITY_KIND[r['commodity']]}:{r['indian_facility']}")
            for node in path:
                G.nodes[node]["routes"].append(r["id"])
            G.add_edges_from(pairwise(path))
            routes[r["id"]] = r | {"path": path}

        G.add_node("gas_grid", kind="gas_grid", name="Pooled gas grid", routes=[])
        for n, kind in list(G.nodes(data="kind")):
            if kind == "lng_terminal":
                G.add_edge(n, "gas_grid")
        for (plant,) in con.execute(
            "SELECT plant_id FROM plant_products WHERE commodity_id = 'urea'"
        ):
            G.add_edge("gas_grid", f"fertilizer_plant:{plant}")

        G.graph["routes"] = routes
        G.graph["factors"] = {r["id"]: r["value"] for r in con.execute("SELECT * FROM factors")}
        G.graph["spr"] = [dict(r) for r in con.execute("SELECT * FROM spr_sites")]
        states: dict[str, dict[str, float]] = defaultdict(dict)  # metric -> state -> value
        for r in con.execute("SELECT state, metric, value FROM state_stats"):
            states[r["metric"]][r["state"]] = r["value"]
        G.graph["states"] = dict(states)
        segments: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for r in con.execute("SELECT fuel, segment, share FROM fuel_segments ORDER BY share DESC"):
            segments[r["fuel"]].append((r["segment"], r["share"]))
        G.graph["segments"] = dict(segments)

        pipelines = {}
        for row in con.execute("SELECT * FROM pipelines"):
            p, key = dict(row), (row["id"],)
            sql = "SELECT {} FROM {} WHERE pipeline_id = ? ORDER BY rowid"
            p["sites"] = [n for (n,) in con.execute(sql.format("node", "pipeline_sites"), key)]
            p["bypasses"] = [
                c for (c,) in con.execute(sql.format("chokepoint_id", "pipeline_bypasses"), key)
            ]
            for a, b in pairwise(
                p["sites"]
            ):  # domestic lines join the sites they link, in flow order
                G.add_edge(a, b, pipeline=p["id"])
            for n in p["sites"]:
                G.nodes[n].setdefault("pipelines", []).append(p["id"])
            pipelines[p["id"]] = p
        G.graph["pipelines"] = pipelines
        sea: dict[str, list[tuple[tuple[str, ...], float]]] = defaultdict(list)
        for row in con.execute("SELECT id, leg, nm FROM sea_paths ORDER BY nm"):
            passes = con.execute(
                "SELECT chokepoint_id FROM sea_path_chokepoints WHERE sea_path_id = ?", (row["id"],)
            )
            sea[row["leg"]].append((tuple(sorted(c for (c,) in passes)), row["nm"]))
        G.graph["sea_paths"] = dict(sea)  # leg (route id or pipeline>port) -> [(chokepoints, nm)]
        return G
    finally:
        con.close()


def resolve(G: nx.DiGraph, node: str) -> str:
    """Accept 'chokepoint:hormuz' or a bare id like 'hormuz', 'sikka', 'QA'."""
    if node in G:
        return node
    for kind in ("chokepoint", "port", "supplier", "refinery", "lng_terminal", "fertilizer_plant"):
        if f"{kind}:{node}" in G:
            return f"{kind}:{node}"
    raise KeyError(f"unknown node {node!r}")


def totals(G: nx.DiGraph) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in G.graph["routes"].values():
        out[r["commodity"]] += r["volume"] or 0
    return dict(out)


def exposure(G: nx.DiGraph, node: str) -> dict[str, dict]:
    """Annual MMT per commodity on the routes through a node, and its share of India's imports."""
    node = resolve(G, node)
    flows: dict[str, float] = defaultdict(float)
    for rid in G.nodes[node]["routes"]:
        r = G.graph["routes"][rid]
        flows[r["commodity"]] += r["volume"] or 0
    all_ = totals(G)
    return {c: {"mmt": round(v, 2), "share": round(v / all_[c], 3)} for c, v in flows.items()}


def critical(G: nx.DiGraph, top: int = 5) -> list[dict]:
    """Chokepoints and ports ranked by the largest import share of any one commodity they carry."""
    betweenness = nx.betweenness_centrality(G)
    rows = []
    for n, d in G.nodes(data=True):
        if d["kind"] not in ("chokepoint", "port") or not d["routes"]:
            continue
        commodity, flow = max(exposure(G, n).items(), key=lambda kv: kv[1]["share"])
        rows.append(
            {
                "node": n,
                "name": d["name"],
                "peak_commodity": commodity,
                "peak_share": flow["share"],
                "betweenness": round(betweenness[n], 4),
            }
        )
    return sorted(rows, key=lambda r: -r["peak_share"])[:top]
