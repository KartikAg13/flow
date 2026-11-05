"""graph-sim-mcp: NetworkX exposure, critical nodes and chokepoint-closure simulation."""

from __future__ import annotations

from functools import cache

from mcp.server.mcpserver import MCPServer

from flow import graph, sim

mcp = MCPServer(
    "graph-sim-mcp",
    instructions="Supply-network analysis of India's critical imports. Node ids: chokepoints "
    "hormuz, bab_el_mandeb, suez, malacca, cape; Indian ports like sikka, dahej, kandla; "
    "suppliers by ISO code like QA, SA, RU.",
)


@cache
def _graph():
    return graph.build_graph()  # seed data is static for the life of the process


@mcp.tool()
def exposure(node: str) -> dict:
    """Annual import volume (MMT) and share of India's imports, per commodity, on the routes
    through one node (chokepoint id, Indian port id or supplier ISO code)."""
    return graph.exposure(_graph(), node)


@mcp.tool()
def critical_nodes(top: int = 5) -> list[dict]:
    """Chokepoints and Indian ports ranked by the largest share of any single commodity they
    carry, with NetworkX betweenness centrality."""
    return graph.critical(_graph(), top)


@mcp.tool()
def simulate_closure(chokepoints: list[str], months: float = 6.0) -> dict:
    """Close one or more chokepoints for N months. Returns lost MMT per commodity, affected
    Indian ports and facilities, the LNG -> urea cascade, strategic petroleum reserve cover
    and unaffected alternative suppliers."""
    return sim.close(_graph(), chokepoints, months)


@mcp.tool()
def closure_impact(chokepoints: list[str], months: float = 6.0) -> dict:
    """Who and where a closure hurts: states whose ports and plants lose cargo or urea output,
    states that run short of diesel, petrol and fertilizer, fuel lost per user segment (trucks,
    buses, cars, two-wheelers, tractors), farm holdings affected and city gas lost."""
    return sim.impact(_graph(), chokepoints, months)


@mcp.tool()
def reroute_options(chokepoints: list[str], months: float = 6.0) -> dict:
    """Alternative routes when chokepoints close: sea detours with extra days, the Saudi and UAE
    pipelines that bypass Hormuz, cargo with no way around, and the open import points with
    domestic pipelines inland. Gives how much of each commodity is recovered."""
    return sim.reroute(_graph(), chokepoints, months)


if __name__ == "__main__":
    mcp.run("stdio")
