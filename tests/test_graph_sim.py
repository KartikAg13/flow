import pytest

from flow.data.build import build
from flow.graph import build_graph, critical, exposure
from flow.sim import close, impact, reroute


@pytest.fixture(scope="module")
def G(tmp_path_factory):
    return build_graph(build(tmp_path_factory.mktemp("db") / "flow.db"))


def test_hormuz_exposure_matches_seed_routes(G) -> None:
    e = exposure(G, "hormuz")
    assert e["crude_oil"]["mmt"] == pytest.approx(108.3, abs=0.1)
    assert e["lng"]["share"] == pytest.approx(0.52, abs=0.01)
    assert set(exposure(G, "kandla")) == {"urea", "dap", "mop"}
    assert critical(G, 3)[0]["peak_share"] >= critical(G, 3)[-1]["peak_share"]


def test_six_month_hormuz_closure(G) -> None:
    r = close(G, ["hormuz"], 6)
    lost = {c["commodity"]: c["lost_mmt"] for c in r["commodities"]}
    assert lost["crude_oil"] == pytest.approx(54.16, abs=0.05)
    assert {f["id"] for f in r["facilities"]} >= {"jamnagar_dta", "vadinar_ref", "koyali"}
    urea = lost["lng"] * 0.31 * 12.3 / 6.2  # factors.json: gas share, LNG and urea Gcal per t
    assert r["cascade"]["urea_output_at_risk_mmt"] == pytest.approx(urea, abs=0.05)
    assert r["spr"]["days_of_lost_crude_covered"] == pytest.approx(18.0, abs=0.5)
    assert all("hormuz" not in a["via"] for a in r["alternatives"]["crude_oil"])


def test_closure_only_accepts_chokepoints(G) -> None:
    assert [c["commodity"] for c in close(G, ["bab_el_mandeb"], 3)["commodities"]] == ["mop"]
    with pytest.raises(ValueError):
        close(G, ["sikka"])
    with pytest.raises(KeyError):
        close(G, ["atlantis"])


def test_hormuz_impact_lands_in_gujarat_and_reaches_people(G) -> None:
    i = impact(G, ["hormuz"], 6)
    assert i["states_hit"][0]["state"] == "Gujarat"  # every Hormuz route ends at a Gujarat site
    # (54.16 crude lost - 5.33 SPR) x 0.443 diesel yield - 28.2 / 2 exports stopped
    diesel = i["fuel"]["diesel"]
    assert diesel["short_mmt"] == pytest.approx((54.16 - 5.33) * 0.443 - 14.1, abs=0.05)
    assert sum(s["kt"] for s in diesel["segments"]) == pytest.approx(
        diesel["short_mmt"] * 1000, rel=0.01
    )
    assert i["fuel_short_states"][0]["state"] == "Uttar Pradesh"
    assert 0 < i["farm_holdings_affected"] < 146_453_741  # Agriculture Census 2015-16 total
    assert all(0 <= f["share_of_use"] <= 1 for f in i["fertilizer"].values())
    assert impact(G, ["suez"], 3)["states_hit"] == []  # no Indian route uses Suez


def test_reroutes_use_bypass_pipelines_and_sea_detours(G) -> None:
    for rid, r in G.graph["routes"].items():  # every seeded path is one searoute actually finds
        if rid in G.graph["sea_paths"]:
            assert tuple(sorted(r["chokepoints"])) in [p for p, _ in G.graph["sea_paths"][rid]]
    r = reroute(G, ["hormuz"], 6)
    assert {b["supplier"] for b in r["bypasses"]} == {"Saudi Arabia", "United Arab Emirates"}
    # India's share of EIA's 2.6 mb/d spare: 108.3 / (14.5 x 365 / 7.33) of it, over half a year
    india = 108.3 / (14.5 * 365 / 7.33) * 2.6 * 365 / 7.33 / 2
    assert sum(b["mmt"] for b in r["bypasses"]) == pytest.approx(india, rel=0.02)
    assert "Iraq" in {s["supplier"] for s in r["stranded"]}  # Basrah has no way around Hormuz
    crude = next(c for c in r["recovered"] if c["commodity"] == "crude_oil")
    assert crude["still_lost_mmt"] == pytest.approx(crude["lost_mmt"] - crude["recovered_mmt"])
    m = reroute(G, ["malacca"], 3)
    assert all(d["via"] == ["Sunda or Lombok Strait"] and d["extra_days"] > 0 for d in m["detours"])
    assert G.has_edge("port:mundra", "refinery:panipat")  # Mundra-Panipat pipeline
