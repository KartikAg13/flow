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
    """Download GDELT 2.0 GKG, filter, write data/raw/events.jsonl."""
    from flow.data.gdelt import fetch

    path = fetch(slices=slices)
    n = sum(1 for _ in path.open(encoding="utf-8"))
    typer.echo(f"{n} events -> {path}")


@data_app.command("build")
def build_db() -> None:
    """Rebuild data/flow.db from seed JSON (and events.jsonl if present)."""
    from flow.data.build import build

    path = build()
    typer.echo(f"built {path}")
