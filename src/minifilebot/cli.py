"""Typer entry point for the minifilebot CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .core import PlanItem, apply_plan, build_plan
from .display import PlanRow, render_summary, render_table
from .matcher import force_match
from .scanner import scan
from .tmdb import TmdbClient, TmdbError

app = typer.Typer(
    name="minifilebot",
    help="Rename anime/TV episode files using TMDB metadata.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


@app.command()
def rename(
    path: Path = typer.Argument(..., exists=True, help="Directory or file to process."),
    apply: bool = typer.Option(False, "--apply", help="Actually rename files (default: dry-run)."),
    tmdb_id: int | None = typer.Option(
        None, "--tmdb-id", help="Force a specific TMDB TV id, skipping auto-match."
    ),
    lang: str = typer.Option("en-US", "--lang", help="TMDB metadata language."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt on --apply."),
    on_conflict: str = typer.Option(
        "suffix",
        "--on-conflict",
        help="When the target file already exists: skip | suffix | overwrite.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging."),
) -> None:
    """Rename video files in PATH based on TMDB metadata."""
    files = scan(path)
    if not files:
        console.print("[yellow]No video files found.[/]")
        raise typer.Exit(code=0)

    try:
        client = TmdbClient(lang=lang)
    except TmdbError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc

    forced = force_match(tmdb_id, client=client) if tmdb_id is not None else None
    if forced is not None and verbose:
        console.print(f"[dim]Forcing match: {forced.name} (tmdb_id={forced.tmdb_id})[/]")

    root = path if path.is_dir() else path.parent
    plan = build_plan(
        files=files,
        client=client,
        forced=forced,
        on_conflict=on_conflict,
        verbose=verbose,
    )

    rows = [
        PlanRow(
            source=item.source,
            target_name=item.target.name if item.target else None,
            status=item.status,
            detail=item.detail,
        )
        for item in plan
    ]
    render_table(rows, console)
    render_summary(rows, console)

    if not apply:
        console.print("\n[dim]Dry-run only. Re-run with --apply to rename.[/]")
        raise typer.Exit(code=0)

    to_apply: list[PlanItem] = [
        item for item in plan if item.status == "OK" and item.target is not None
    ]
    if not to_apply:
        console.print("[yellow]Nothing to apply.[/]")
        raise typer.Exit(code=0)

    if not yes:
        confirmed = typer.confirm(f"Rename {len(to_apply)} file(s)?", default=False)
        if not confirmed:
            console.print("[yellow]Aborted.[/]")
            raise typer.Exit(code=1)

    renames, history_path = apply_plan(to_apply, root=root)
    if renames and history_path is not None:
        console.print(f"[green]Renamed {len(renames)} file(s).[/] History: {history_path}")
    else:
        console.print("[yellow]No files needed renaming.[/]")


if __name__ == "__main__":
    app()
