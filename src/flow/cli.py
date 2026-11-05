"""CLI entrypoint."""

from __future__ import annotations

import json

import typer

from flow import __version__

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Flow: critical-import resilience (oil, LNG, fertilizers).",
)
data_app = typer.Typer(no_args_is_help=True, help="Fetch data.")
app.add_typer(data_app, name="data")
mcp_app = typer.Typer(no_args_is_help=True, help="Run an MCP server over stdio.")
app.add_typer(mcp_app, name="mcp")


def _echo(data) -> None:
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


def _rescore() -> dict:
    from flow import intel
    from flow.data.build import connect

    con = connect()
    try:
        return intel.store(con)
    finally:
        con.close()


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@data_app.command("gdelt")
def gdelt(
    slices: int = typer.Option(1, min=1, help="How many 15-minute GKG slices to pull."),
) -> None:
    """Download GDELT 2.0 GKG, filter, write data/raw, insert into flow.db and rescore risk."""
    from flow.data.build import append_events
    from flow.data.gdelt import fetch

    path = fetch(slices=slices)
    events = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    inserted = append_events(events)
    typer.echo(f"{len(events)} events -> {path} (inserted {inserted} new into data/flow.db)")
    typer.echo(f"risk: {_rescore()}")


@data_app.command("refilter")
def refilter_cmd() -> None:
    """Re-download the slices in data/raw, apply the current news filter, rebuild flow.db."""
    from flow.data.build import build
    from flow.data.gdelt import refilter

    for name, (before, after) in refilter().items():
        typer.echo(f"{name}: {before} -> {after} events")
    typer.echo(f"built {build()}")
    typer.echo(f"risk: {_rescore()}")


@data_app.command("build")
def build_db() -> None:
    """Rebuild data/flow.db from seed JSON (and data/raw/events*.jsonl), then score risk."""
    from flow.data.build import build

    path = build()
    typer.echo(f"built {path}")
    typer.echo(f"risk: {_rescore()}")


@data_app.command("ingest")
def ingest_cmd(
    path: str | None = typer.Option(
        None,
        "--file",
        "-f",
        help="JSONL file to append. If omitted, appends from data/raw/events.jsonl.",
    ),
) -> None:
    """Incrementally append events into data/flow.db without rebuilding the database."""
    from pathlib import Path

    from flow.data.build import append_events, repo_root

    target = Path(path) if path else (repo_root() / "data" / "raw" / "events.jsonl")
    if not target.exists():
        typer.echo(f"File not found: {target}")
        raise typer.Exit(1)

    inserted = append_events(target)
    typer.echo(f"Appended {inserted} new events to data/flow.db from {target}")
    typer.echo(f"risk: {_rescore()}")


@app.command()
def risk() -> None:
    """Recompute live chokepoint risk (0-100) and store it in entity_risk."""
    _echo(_rescore())


def _on_graph(fn, *args) -> None:
    from flow.graph import build_graph

    try:
        _echo(fn(build_graph(), *args))
    except (KeyError, ValueError) as e:
        typer.echo(f"error: {str(e).strip(chr(34))}", err=True)
        raise typer.Exit(1) from None


@app.command()
def exposure(node: str = typer.Argument(..., help="hormuz, sikka, QA, ...")) -> None:
    """Annual MMT and import share per commodity through a chokepoint, port or supplier."""
    from flow import graph

    _on_graph(graph.exposure, node)


@app.command()
def critical(top: int = 5) -> None:
    """Chokepoints and ports ranked by the largest single-commodity share they carry."""
    from flow import graph

    _on_graph(graph.critical, top)


@app.command()
def simulate(
    chokepoints: list[str] = typer.Argument(..., help="One or more: hormuz bab_el_mandeb ..."),
    months: float = typer.Option(6.0, help="Closure length in months."),
) -> None:
    """Deterministic closure scenario: lost volumes, facilities, cascade, SPR, alternatives."""
    from flow import sim

    _on_graph(sim.close, chokepoints, months)


@app.command()
def impact(
    chokepoints: list[str] = typer.Argument(..., help="One or more: hormuz bab_el_mandeb ..."),
    months: float = typer.Option(6.0, help="Closure length in months."),
) -> None:
    """Who a closure hurts: states hit and short, fuel per user segment, farm holdings."""
    from flow import sim

    _on_graph(sim.impact, chokepoints, months)


@app.command()
def reroute(
    chokepoints: list[str] = typer.Argument(..., help="One or more: hormuz bab_el_mandeb ..."),
    months: float = typer.Option(6.0, help="Closure length in months."),
) -> None:
    """Alternative routes: sea detours, bypass pipelines, stranded cargo, open entry points."""
    from flow import sim

    _on_graph(sim.reroute, chokepoints, months)


@app.command()
def ask(question: str) -> None:
    """Ask the multi-agent Copilot (needs GROQ_API_KEY in .env). Writes a trace to artifacts/."""
    import asyncio

    from flow.agents import ask as run

    try:
        result = asyncio.run(run(question))
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(1) from None
    typer.echo(result["answer"])
    typer.echo(f"\ntrace: {result['trace']}")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Serve the API and the built dashboard (frontend/dist)."""
    from flow.api import serve as run

    run(host, port)


@mcp_app.command("world")
def mcp_world() -> None:
    """world-model-mcp: risk scores, news, import mix, read-only SQL."""
    from flow.mcp.world import mcp

    mcp.run("stdio")


@mcp_app.command("graph")
def mcp_graph() -> None:
    """graph-sim-mcp: exposure, critical nodes, closure simulation."""
    from flow.mcp.graph_sim import mcp

    mcp.run("stdio")
