"""Cascade simulation: close chokepoints for N months and count what India stops receiving, then
where that shortfall lands and who runs short (states, fuel users, farm holdings)."""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

from flow.graph import resolve, totals

ASSUMPTION = (
    "A closed chokepoint blocks every route through it for the whole period (no detours). "
    "Volumes are 2024 annual flows, prorated by months. LNG loss is spread pro rata across "
    "gas users, so fertilizer loses its share; urea output follows the NUP-2015 energy norm."
)
IMPACT_ASSUMPTION = (
    "Each shortfall is shared pro rata: every state and every user segment loses the same share "
    "of its normal use. The SPR is drawn in full and fuel exports stop before domestic supply is "
    "cut. Refinery yields, exports and state and segment shares are the latest published values; "
    "state fertilizer shares come from Kharif 2026 sales. Farm holdings affected = a state's "
    "holdings x the share of its fertilizer that goes missing."
)


def _blocked(G: nx.DiGraph, chokepoints: list[str]) -> tuple[list[str], set[str]]:
    """Validated chokepoint nodes and the ids of every route through them."""
    if not chokepoints:
        raise ValueError("name at least one chokepoint")
    nodes = [resolve(G, c) for c in chokepoints]
    if any(G.nodes[n]["kind"] != "chokepoint" for n in nodes):
        raise ValueError(f"not a chokepoint: {chokepoints}")
    return nodes, {rid for n in nodes for rid in G.nodes[n]["routes"]}


def close(G: nx.DiGraph, chokepoints: list[str], months: float = 6.0) -> dict:
    if not 0 < months <= 24:
        raise ValueError("months must be in (0, 24]")
    nodes, blocked = _blocked(G, chokepoints)
    routes = G.graph["routes"]
    frac = months / 12
    name = lambda node: G.nodes[node]["name"]  # noqa: E731

    lost: dict[str, float] = defaultdict(float)
    by_port: dict[str, float] = defaultdict(float)
    by_facility: dict[str, float] = defaultdict(float)
    for rid in blocked:
        r = routes[rid]
        v = (r["volume"] or 0) * frac
        lost[r["commodity"]] += v
        by_port[r["path"][-2] if r["indian_facility"] else r["path"][-1]] += v
        if r["indian_facility"]:
            by_facility[r["path"][-1]] += v

    all_ = totals(G)
    f = G.graph["factors"]
    lng_lost = lost.get("lng", 0.0)
    gas_to_fertilizer = lng_lost * f["fertilizer_gas_share"]
    urea_lost = gas_to_fertilizer * f["lng_gcal_per_t"] / f["urea_gcal_per_t"]
    spr_mmt = sum(s["capacity_mmt"] for s in G.graph["spr"])
    crude_per_day = lost.get("crude_oil", 0.0) / (months * 365 / 12)

    # Inland sites that domestic pipelines feed from an import point (port, LNG terminal) that
    # lost cargo
    hit = set(by_port) | {n for n in by_facility if G.nodes[n]["kind"] == "lng_terminal"}
    inland = lambda xs: [x for x in xs if G.nodes[x]["kind"] not in ("port", "lng_terminal")]  # noqa: E731
    downstream = [
        {"from": name(n), "pipeline": p["name"]}
        | {"sites": [{"name": name(x), "state": G.nodes[x]["state"]} for x in after]}
        for p in G.graph["pipelines"].values()
        for i, n in enumerate(p["sites"])
        if n in hit and (after := inland(p["sites"][i + 1 :]))
    ]

    def top(d: dict[str, float]) -> list[dict]:
        rows = sorted(d.items(), key=lambda kv: -kv[1])
        return [
            {"id": k.split(":")[1], "name": name(k), "state": G.nodes[k]["state"]}
            | {"lost_mmt": round(v, 2)}
            for k, v in rows
        ]

    alternatives = {
        c: [
            {
                "supplier": name(r["path"][0]),
                "mmt_per_year": round(r["volume"], 2),
                "via": r["chokepoints"] or ["direct"],
            }
            for rid, r in routes.items()
            if r["commodity"] == c and rid not in blocked
        ][:4]
        for c in lost
    }
    return {
        "closed": [name(n) for n in nodes],
        "months": months,
        "commodities": [
            {
                "commodity": c,
                "lost_mmt": round(v, 2),
                "share_of_imports": round(v / (all_[c] * frac), 3),
            }
            for c, v in sorted(lost.items(), key=lambda kv: -kv[1] / all_[kv[0]])
        ],
        "ports": top(by_port),
        "facilities": top(by_facility),
        "downstream": downstream,
        "cascade": {
            "lng_lost_mmt": round(lng_lost, 2),
            "fertilizer_gas_lost_mmt_lng": round(gas_to_fertilizer, 2),
            "urea_output_at_risk_mmt": round(urea_lost, 2),
        },
        "spr": {
            "capacity_mmt": spr_mmt,
            "days_of_lost_crude_covered": round(spr_mmt / crude_per_day, 1)
            if crude_per_day
            else None,
            "sites": [s["name"] for s in G.graph["spr"]],
        },
        "alternatives": alternatives,
        "assumption": ASSUMPTION,
    }


def impact(G: nx.DiGraph, chokepoints: list[str], months: float = 6.0) -> dict:
    """Where a closure lands (states whose ports and plants lose cargo or urea output) and who
    runs short of fuel and fertilizer (states, vehicle and other user segments, farm holdings)."""
    s = close(G, chokepoints, months)
    _, blocked = _blocked(G, chokepoints)
    f, stats, frac = G.graph["factors"], G.graph["states"], months / 12
    lost = {c["commodity"]: c["lost_mmt"] for c in s["commodities"]}
    urea_at_risk = s["cascade"]["urea_output_at_risk_mmt"]

    # Where it lands: cargo lost at each state's ports and plants, and urea output at risk there
    lands: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for rid in blocked:
        r = G.graph["routes"][rid]
        lands[G.nodes[r["path"][-1]]["state"]][r["commodity"]] += (r["volume"] or 0) * frac
    output = stats["urea_production"]
    for st, v in output.items():
        lands[st]["urea_output"] += urea_at_risk * v / sum(output.values())

    def spread(metric: str, national_mmt: float) -> dict[str, float]:
        col = stats[metric]
        return {st: national_mmt * v / sum(col.values()) for st, v in col.items()}

    # Fuel: crude after the SPR, times refinery yield, minus the exports India would stop first
    crude = max(0.0, lost.get("crude_oil", 0.0) - s["spr"]["capacity_mmt"])
    fuel_use = {fu: sum(stats[fu].values()) / 1000 * frac for fu in ("diesel", "petrol")}
    fuel_short = {
        fu: min(use, max(0.0, crude * f[f"{fu}_yield"] - f[f"{fu}_exports_mmt"] * frac))
        for fu, use in fuel_use.items()
    }
    # Fertilizer: imports lost plus (for urea) domestic output lost to the gas cascade
    fert_need = {c: f[f"{c}_consumption_mmt"] * frac for c in ("urea", "dap", "mop")}
    fert_lost = {c: lost.get(c, 0.0) + (urea_at_risk if c == "urea" else 0.0) for c in fert_need}
    fert_share = {c: min(1.0, fert_lost[c] / need) for c, need in fert_need.items()}

    by_state_fuel = {fu: spread(fu, fuel_short[fu]) for fu in fuel_use}
    by_state_fert = {c: spread(f"{c}_sales", need) for c, need in fert_need.items()}
    rows = []
    for st in stats["diesel"].keys() | stats["farm_holdings"].keys():
        use = sum(by_state_fert[c].get(st, 0.0) for c in fert_need)
        short = sum(fert_share[c] * by_state_fert[c].get(st, 0.0) for c in fert_need)
        holdings = stats["farm_holdings"].get(st, 0.0)
        rows.append(
            {
                "state": st,
                "diesel_kt": round(by_state_fuel["diesel"].get(st, 0.0) * 1000),
                "petrol_kt": round(by_state_fuel["petrol"].get(st, 0.0) * 1000),
                "fertilizer_kt": round(short * 1000),
                "farm_holdings": round(holdings * short / use) if use else 0,
            }
        )

    def top(key, n: int = 8) -> list[dict]:
        return sorted((r for r in rows if key(r)), key=key, reverse=True)[:n]

    days = months * 365 / 12
    plants = [G.nodes[n] for n in G.successors("gas_grid")]
    return {
        "closed": s["closed"],
        "months": months,
        "states_hit": [
            {"state": st, "lost_mmt": round(sum(by.values()), 2)}
            | {"by": {c: round(v, 2) for c, v in sorted(by.items(), key=lambda kv: -kv[1])}}
            for st, by in sorted(lands.items(), key=lambda kv: -sum(kv[1].values()))
            if sum(by.values()) > 0
        ][:8],
        "fuel_short_states": top(lambda r: r["diesel_kt"] + r["petrol_kt"]),
        "farm_short_states": top(lambda r: r["farm_holdings"]),
        "fuel": {
            fu: {
                "short_mmt": round(short, 2),
                "share_of_use": round(short / fuel_use[fu], 3),
                "days_of_use_lost": round(short / fuel_use[fu] * days, 1),
                "segments": [
                    {"segment": name, "kt": round(short * share * 1000)}
                    for name, share in G.graph["segments"][fu]
                ],
            }
            for fu, short in fuel_short.items()
        },
        "fertilizer": {
            c: {"short_mmt": round(fert_lost[c], 2), "share_of_use": round(fert_share[c], 3)}
            for c in fert_need
        },
        "farm_holdings_affected": sum(r["farm_holdings"] for r in rows),
        "city_gas_lost_mmt_lng": round(lost.get("lng", 0.0) * f["cgd_gas_share"], 2),
        "power_gas_lost_mmt_lng": round(lost.get("lng", 0.0) * f["power_gas_share"], 2),
        "urea_plants": {
            "output_lost_share": round(urea_at_risk / (sum(output.values()) / 10 * frac), 3),
            "plants": [{"name": d["name"], "state": d["state"]} for d in plants],
        },
        "assumption": IMPACT_ASSUMPTION,
    }


SPEED_KNOTS = 14  # laden tanker service speed; EIA's "about 15 days" extra via the Cape agrees
REROUTE_ASSUMPTION = (
    "Ships take the shortest sea path that avoids every closed chokepoint (searoute on the "
    "Eurostat SeaRoute network, 14 knots); the first cargo arrives later by the extra sailing "
    "time, and that part of the period stays lost. India gets the share of EIA's ~2.6 million b/d "
    "spare bypass pipeline capacity that matches its share of Hormuz crude flows. Freight, "
    "insurance and whether suppliers will sell are not modelled."
)


def reroute(G: nx.DiGraph, chokepoints: list[str], months: float = 6.0) -> dict:
    """Alternative routes for the cargo a closure blocks: sea detours, bypass pipelines, and the
    import points and domestic pipelines that stay open."""
    s = close(G, chokepoints, months)
    nodes, blocked = _blocked(G, chokepoints)
    shut = {G.nodes[n]["id"] for n in nodes}
    f, routes, paths = G.graph["factors"], G.graph["routes"], G.graph["sea_paths"]
    frac, days, per_day = months / 12, months * 365 / 12, SPEED_KNOTS * 24
    name = lambda node: G.nodes[node]["name"]  # noqa: E731

    def via(passes: tuple[str, ...], route_cps: list[str]) -> list[str]:
        if passes:
            return [name(f"chokepoint:{c}") for c in passes]
        return ["Sunda or Lombok Strait"] if "malacca" in route_cps else ["open sea"]

    def open_path(leg: str) -> tuple[tuple[str, ...], float] | None:
        return next(((p, nm) for p, nm in paths.get(leg, []) if not set(p) & shut), None)

    def arriving(mmt: float, extra_days: float) -> float:  # cargo that still lands in the period
        return mmt * max(0.0, 1 - max(extra_days, 0.0) / days)

    detours, stuck = [], []
    for rid in sorted(blocked, key=lambda r: -(routes[r]["volume"] or 0)):
        r, mmt = routes[rid], (routes[rid]["volume"] or 0) * frac
        base = next(
            (nm for p, nm in paths.get(rid, []) if list(p) == sorted(r["chokepoints"])), None
        )
        alt = open_path(rid)
        if base and alt:
            extra = (alt[1] - base) / per_day
            detours.append(
                {
                    "supplier": name(r["path"][0]),
                    "commodity": r["commodity"],
                    "to": name(r["path"][-1]),
                    "mmt": round(mmt, 2),
                    "via": via(alt[0], r["chokepoints"]),
                    "extra_nm": round(alt[1] - base),
                    "extra_days": round(extra, 1),
                    "recovered_mmt": round(arriving(mmt, extra), 2),
                }
            )
        else:
            stuck.append(rid)

    # Bypass pipelines: India's share of the spare capacity, split over the routes they can carry
    bypasses = []
    pipes = [
        p for p in G.graph["pipelines"].values() if p["scope"] == "bypass" and p["supplier_iso"]
    ]
    usable = {
        rid: p
        for rid in stuck
        for p in pipes
        if routes[rid]["commodity"] == "crude_oil"
        and routes[rid]["supplier_iso"] == p["supplier_iso"]
        and shut & set(routes[rid]["chokepoints"]) <= set(p["bypasses"])
    }
    if usable:
        mmt_per_mbpd = 365 / f["crude_bbl_per_t"]  # 1 million b/d as million tonnes a year
        india = sum(
            r["volume"]
            for r in routes.values()
            if r["commodity"] == "crude_oil" and "hormuz" in r["chokepoints"]
        )
        share = india / (f["hormuz_crude_mbpd"] * mmt_per_mbpd)
        budget = f["hormuz_bypass_spare_mbpd"] * mmt_per_mbpd * share * frac
        want = {rid: routes[rid]["volume"] * frac for rid in usable}
        for rid, p in usable.items():
            r = routes[rid]
            alloc = min(want[rid], budget * want[rid] / sum(want.values()))
            outlet = open_path(f"{p['id']}>{r['indian_port']}")
            base = next((nm for _, nm in paths.get(rid, [])), None)
            if not outlet or not alloc:
                continue
            extra = (outlet[1] - base) / per_day if base else 0.0
            stuck.remove(rid)
            bypasses.append(
                {
                    "pipeline": p["name"],
                    "supplier": name(r["path"][0]),
                    "outlet": p["end_name"],
                    "via": via(outlet[0], []),
                    "mmt": round(alloc, 2),
                    "of_blocked_mmt": round(want[rid], 2),
                    "extra_days": round(extra, 1),
                    "recovered_mmt": round(arriving(alloc, extra), 2),
                }
            )

    recovered: dict[str, float] = defaultdict(float)
    for d in detours:
        recovered[d["commodity"]] += d["recovered_mmt"]
    for b in bypasses:
        recovered["crude_oil"] += b["recovered_mmt"]

    # Import points with no blocked cargo, and the domestic pipelines that carry from them inland
    hit = {n for rid in blocked for n in routes[rid]["path"]}
    entry = [
        {"site": name(n), "state": G.nodes[n]["state"], "fluid": p["fluid"], "pipeline": p["name"]}
        | {
            "reaches": [
                name(x) for x in p["sites"] if G.nodes[x]["kind"] not in ("port", "lng_terminal")
            ]
        }
        for p in G.graph["pipelines"].values()
        if p["scope"] == "domestic"
        for n in p["sites"][:1]
        if n not in hit and G.nodes[n]["kind"] in ("port", "lng_terminal")
    ]
    return {
        "closed": s["closed"],
        "months": months,
        "detours": detours,
        "bypasses": bypasses,
        "stranded": [
            {"supplier": name(routes[r]["path"][0]), "commodity": routes[r]["commodity"]}
            | {"mmt": round((routes[r]["volume"] or 0) * frac, 2)}
            | {"reason": "no sea route or pipeline around" if r in paths else "origin not known"}
            for r in stuck
        ],
        "recovered": [
            {"commodity": c["commodity"], "lost_mmt": c["lost_mmt"]}
            | {"recovered_mmt": round(recovered[c["commodity"]], 2)}
            | {"still_lost_mmt": round(max(0.0, c["lost_mmt"] - recovered[c["commodity"]]), 2)}
            for c in s["commodities"]
        ],
        "entry_points": entry,
        "assumption": REROUTE_ASSUMPTION,
    }
