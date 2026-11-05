"""HTTP API for the dashboard, plus the built frontend (frontend/dist). Stdlib only.

GET  /api/dashboard           chokepoints with live risk, history and exposure; ports; routes
GET  /api/news?entity=&limit= latest GDELT articles, deduplicated by headline
GET  /api/sim?chokepoints=hormuz&months=6   deterministic closure scenario
POST /api/ask {"question": "..."}           multi-agent Copilot (needs GROQ_API_KEY)
"""

from __future__ import annotations

import asyncio
import json
import re
import threading
from collections import defaultdict
from contextlib import closing
from difflib import get_close_matches
from functools import cache, lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from flow import graph, intel, sim
from flow.data.build import connect, default_db, repo_root

DIST = repo_root() / "frontend" / "dist"
FACILITY_KINDS = ("refinery", "lng_terminal", "fertilizer_plant")


def version() -> int:
    """Changes whenever flow.db does (GDELT ingest, rescore, rebuild), so it keys every cache."""
    connect().close()  # builds flow.db on first use
    return default_db().stat().st_mtime_ns


@lru_cache(maxsize=1)
def _graph(_version: int):
    return graph.build_graph()


def _pick(d: dict, *keys: str) -> dict:
    return {k: d[k] for k in keys}


def dashboard() -> dict:
    G = _graph(version())
    with closing(connect()) as con:
        risk, hist = intel.scores(con), intel.history(con)
        as_of, n = con.execute("SELECT max(observed_at), count(*) FROM events").fetchone()

    nodes = lambda kind: [d for _, d in G.nodes(data=True) if d["kind"] == kind]  # noqa: E731
    lanes: dict[tuple[str, str], dict] = {}
    for r in G.graph["routes"].values():
        for c in r["chokepoints"]:
            lane = lanes.setdefault((c, r["indian_port"]), {"mmt": 0.0, "commodities": set()})
            lane["mmt"] += r["volume"] or 0
            lane["commodities"].add(r["commodity"])
    via: dict[str, list[str]] = defaultdict(list)
    for c, port in lanes:
        via[port].append(c)

    return {
        "as_of": as_of,
        "events": n,
        "chokepoints": [
            _pick(d, "id", "name", "lat", "lon", "transit_volume", "transit_unit", "year")
            | _pick(d, "source", "source_url")
            | {
                "risk": risk[d["id"]],
                "history": hist[d["id"]],
                "exposure": graph.exposure(G, f"chokepoint:{d['id']}"),
                "ports": sorted({p for c, p in lanes if c == d["id"]}),
            }
            for d in nodes("chokepoint")
        ],
        "ports": [
            _pick(d, "id", "name", "lat", "lon", "coast")
            | {"via": sorted(via[d["id"]]), "exposure": graph.exposure(G, f"port:{d['id']}")}
            for d in nodes("port")
        ],
        "lanes": [
            {"chokepoint": c, "port": p, "mmt": round(v["mmt"], 2)}
            | {"commodities": sorted(v["commodities"])}
            for (c, p), v in lanes.items()
        ],
        "facilities": [
            _pick(d, "id", "name", "lat", "lon", "kind") for k in FACILITY_KINDS for d in nodes(k)
        ]
        + [{**_pick(s, "id", "name", "lat", "lon"), "kind": "spr"} for s in G.graph["spr"]],
        "critical": graph.critical(G, 5),
        "pipelines": [
            _pick(p, "id", "name", "fluid", "scope", "operator", "capacity", "capacity_unit")
            | {"status": p["status"], "points": _points(G, p)}
            for p in G.graph["pipelines"].values()
        ],
    }


def _points(G, p: dict) -> list[list[float]]:
    """Map polyline: the linked sites in order, or the bypass line's two ends abroad."""
    if p["sites"]:
        return [[G.nodes[n]["lat"], G.nodes[n]["lon"]] for n in p["sites"]]
    return [[p["start_lat"], p["start_lon"]], [p["end_lat"], p["end_lon"]]]


def _norm(text: str) -> str:
    return " " + re.sub(r"[\W_]+", " ", text).lower().strip() + " "


def places(names: list[str]) -> list[dict]:
    """Map place names from a Copilot answer to map nodes ("Bab al-Mandeb" -> bab_el_mandeb)."""
    G = _graph(version())
    kinds = ("chokepoint", "port", *FACILITY_KINDS)
    nodes = [d for _, d in G.nodes(data=True) if d["kind"] in kinds]
    nodes += [s | {"kind": "spr"} for s in G.graph["spr"]]
    keys = [_norm(d["name"]) for d in nodes]
    found: dict[tuple[str, str], dict] = {}
    for name in names:
        n = _norm(name)
        hits = [d for k, d in zip(keys, nodes) if len(n) > 5 and (n in k or k in n)]
        hits = hits or [nodes[keys.index(k)] for k in get_close_matches(n, keys, 1, 0.8)]
        for d in hits:
            found[d["kind"], d["id"]] = _pick(d, "kind", "id", "name")
    return list(found.values())


@cache
def _loop() -> asyncio.AbstractEventLoop:
    """One event loop for every Copilot run: Groq's pooled HTTP client must not outlive its loop."""
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return loop


@lru_cache(maxsize=128)
def _ask(question: str, _version: int) -> dict:
    """One Copilot run per question and db version: a new GDELT slice or rebuild changes the
    version, so a cached answer never outlives the data it was built from."""
    from flow import agents  # heavy imports; only the Copilot needs them

    result = asyncio.run_coroutine_threadsafe(agents.ask(question), _loop()).result()
    return result | {"places": places(result["places"])}


def headline(url: str) -> str:
    """GKG rows carry no headline, so rebuild one from the URL slug."""
    # ponytail: slug heuristic; fetch the page <title> if headlines ever need to be exact
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    slug = re.sub(r"\.\w{2,5}$", "", max(parts, key=lambda p: p.count("-"), default=""))
    words = [w for w in re.split(r"[-_]+", slug) if w and not re.search(r"\d{4,}", w)]
    if len(words) < 3:
        return parsed.netloc.removeprefix("www.")
    text = " ".join(words)
    return text[0].upper() + text[1:]


def news(entity: str | None = None, limit: int = 60) -> list[dict]:
    with closing(connect()) as con:
        rows = con.execute(
            """SELECT e.event_id, e.observed_at, e.source_name, e.url, e.tone,
                 (SELECT group_concat(entity_id) FROM event_entities x
                  WHERE x.event_id = e.event_id) AS entities,
                 (SELECT group_concat(commodity_id) FROM event_commodities x
                  WHERE x.event_id = e.event_id) AS commodities
               FROM events e
               WHERE ?1 IS NULL OR e.event_id IN
                 (SELECT event_id FROM event_entities WHERE entity_id = ?1)
               ORDER BY e.observed_at DESC, e.tone ASC LIMIT 2000""",
            (entity,),
        ).fetchall()
    out, seen = [], set()
    for r in rows:
        title = headline(r["url"])
        if title in seen:  # syndicated copies of one story
            continue
        seen.add(title)
        out.append(
            _pick(dict(r), "event_id", "observed_at", "source_name", "url")
            | {
                "title": title,
                "tone": round(r["tone"] or 0.0, 1),
                "entities": r["entities"].split(",") if r["entities"] else [],
                "commodities": r["commodities"].split(",") if r["commodities"] else [],
            }
        )
        if len(out) >= limit:
            break
    return out


class Handler(SimpleHTTPRequestHandler):
    def _json(self, data, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/api/dashboard":
                return self._json(dashboard())
            if url.path == "/api/news":
                return self._json(news(q.get("entity"), min(int(q.get("limit", 60)), 200)))
            if url.path == "/api/sim":
                chokepoints = [c for c in q.get("chokepoints", "hormuz").split(",") if c]
                G, months = _graph(version()), float(q.get("months", 6))
                scenario = sim.close(G, chokepoints, months)
                extra = {"impact": sim.impact(G, chokepoints, months)}
                extra["reroutes"] = sim.reroute(G, chokepoints, months)
                return self._json(scenario | extra)
        except (KeyError, ValueError) as e:
            return self._json({"error": str(e).strip("'\"")}, 400)
        if url.path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)
        if not DIST.exists():
            return self._json({"error": "frontend not built: cd frontend && npm run build"}, 404)
        return super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/ask":
            return self._json({"error": "not found"}, 404)
        size = int(self.headers.get("Content-Length") or 0)
        if size > 10_000:
            return self._json({"error": "request too large"}, 413)
        try:
            question = str(json.loads(self.rfile.read(size) or b"{}").get("question", "")).strip()
        except (json.JSONDecodeError, AttributeError):
            return self._json({"error": 'send JSON like {"question": "..."}'}, 400)
        if not 0 < len(question) <= 500:
            return self._json({"error": "question must be 1-500 characters"}, 400)
        try:
            key = " ".join(re.sub(r"[^\w\s]", " ", question.lower()).split())
            return self._json(_ask(key, version()))
        except Exception as e:  # surface Groq/MCP failures to the UI instead of a dropped socket
            while isinstance(e, ExceptionGroup):  # MCP's TaskGroup hides the real error
                e = e.exceptions[0]
            msg = str(e)
            if limit := re.search(r"tokens per (minute|day).*?try again in ([\dhm]*\d+)", msg):
                msg = f"Groq's free tier is out of tokens this {limit[1]}; retry in {limit[2]}s."
            return self._json({"error": msg}, 502)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), partial(Handler, directory=str(DIST)))
    print(f"Flow on http://{host}:{port}  (API under /api)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
