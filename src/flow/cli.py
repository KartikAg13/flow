"""CLI entrypoint. Grow commands in the phase that owns them."""

from __future__ import annotations

import typer

from flow import LOCKED, __version__
from flow.system.requirements import LAYERS, NFR, USE_CASES

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Flow: critical-import resilience (oil, LNG, fertilizers).",
)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def direction() -> None:
    """Print the frozen scope so you do not have to open the docs."""
    typer.echo("Flow — locked direction")
    typer.echo(f"  version      {__version__}")
    for key, value in LOCKED.items():
        if isinstance(value, tuple):
            value = ", ".join(value)
        typer.echo(f"  {key:<12} {value}")
    typer.echo("  docs         docs/DIRECTION.md")
    typer.echo("  next step    docs/PHASES.md  (Phase 1, steps 1.1 and 1.2)")
    typer.echo("  design       uv run flow design")


@app.command()
def design() -> None:
    """Print the system-design skeleton (layers, use cases, NFRs)."""
    typer.echo("Layers")
    for layer in LAYERS:
        typer.echo(f"  {layer}")
    typer.echo("Use cases")
    for uc in USE_CASES:
        llm = "llm" if uc.needs_llm else "no-llm"
        typer.echo(f"  {uc.id}  {uc.name}  [{llm}]")
    typer.echo("NFRs")
    for item in NFR:
        typer.echo(f"  {item.id}  {item.quality}: {item.target}")
    typer.echo("docs/SYSTEM-DESIGN.md")
