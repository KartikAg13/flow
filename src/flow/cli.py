"""CLI entrypoint."""

from __future__ import annotations

import typer

from flow import __version__

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Flow: critical-import resilience (oil, LNG, fertilizers).",
)
data_app = typer.Typer(no_args_is_help=True, help="Fetch data.")
app.add_typer(data_app, name="data")


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@data_app.command("gdelt")
def gdelt(
    slices: int = typer.Option(1, min=1, help="How many 15-minute GKG slices to pull."),
) -> None:
    """Download GDELT 2.0 GKG, filter, write data/raw, and insert into flow.db."""
    import json

    from flow.data.build import append_events
    from flow.data.gdelt import fetch

    path = fetch(slices=slices)
    events = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    inserted = append_events(events)
    typer.echo(f"{len(events)} events -> {path} (inserted {inserted} new into data/flow.db)")


@data_app.command("build")
def build_db() -> None:
    """Rebuild data/flow.db from seed JSON (and events.jsonl if present)."""
    from flow.data.build import build

    path = build()
    typer.echo(f"built {path}")


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
