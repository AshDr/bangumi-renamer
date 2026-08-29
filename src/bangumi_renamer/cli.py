"""Typer entry point for the bangumi-renamer CLI."""

from __future__ import annotations

import json
import os
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any

import click
import typer
from rich.console import Console

from . import __version__
from .core import PlanItem, apply_plan, build_plan
from .display import PlanRow, render_plain, render_summary, render_table, summarize_rows
from .matcher import MatchError, force_match
from .scanner import scan
from .tmdb import TmdbClient, TmdbError

app = typer.Typer(
    name="bangumi-renamer",
    help="Rename anime/TV episode videos and external subtitles using TMDB metadata.",
    no_args_is_help=True,
    add_completion=False,
)


class ConflictPolicy(StrEnum):
    SKIP = "skip"
    SUFFIX = "suffix"
    OVERWRITE = "overwrite"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"bangumi-renamer {__version__}")
        raise typer.Exit(code=0)


def _make_console(*, stderr: bool = False, no_color: bool = False) -> Console:
    return Console(stderr=stderr, no_color=no_color)


def _build_rows(plan: list[PlanItem]) -> list[PlanRow]:
    return [
        PlanRow(
            source=item.source,
            target_name=item.target.name if item.target else None,
            status=item.status,
            detail=item.detail,
        )
        for item in plan
    ]


def _emit_plan(
    rows: list[PlanRow],
    *,
    stdout_console: Console,
    output_mode: str,
) -> None:
    if output_mode == "plain":
        render_plain(rows, stdout_console)
        return
    render_table(rows, stdout_console)
    render_summary(rows, stdout_console)


def _json_payload(
    *,
    path: Path,
    rows: list[PlanRow],
    apply_requested: bool,
    applied: bool,
    renames: list[tuple[Path, Path]],
    history_path: Path | None,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "apply_requested": apply_requested,
        "applied": applied,
        "summary": summarize_rows(rows),
        "items": [
            {
                "source": str(row.source),
                "target": row.target_name,
                "status": row.status,
                "detail": row.detail,
            }
            for row in rows
        ],
        "renames": [{"source": str(src), "target": str(dst)} for src, dst in renames],
        "history_path": str(history_path) if history_path is not None else None,
    }


def _suggest_apply(path: Path) -> str:
    return f"Next: run `bangumi-renamer {path} --apply` when the preview looks right."


def _write_json(console: Console, payload: dict[str, Any]) -> None:
    console.file.write(f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n")


@app.command()
def rename(
    path: Path = typer.Argument(..., exists=True, help="Directory or file to process."),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    apply: bool = typer.Option(False, "--apply", help="Actually rename files (default: dry-run)."),
    tmdb_id: int | None = typer.Option(
        None, "--tmdb-id", help="Force a specific TMDB TV id, skipping auto-match."
    ),
    lang: str = typer.Option("en-US", "--lang", help="TMDB metadata language."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt on --apply."),
    plain: bool = typer.Option(
        False,
        "--plain",
        help="Emit stable tab-separated output for scripts.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit structured JSON output.",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors."),
    no_input: bool = typer.Option(
        False,
        "--no-input",
        help="Disable interactive prompts; fail instead.",
    ),
    debug: bool = typer.Option(False, "--debug", help="Show tracebacks for unexpected errors."),
    on_conflict: ConflictPolicy = typer.Option(
        ConflictPolicy.SUFFIX,
        "--on-conflict",
        help="When the target file already exists.",
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging."),
) -> None:
    """Rename episode videos and external subtitles in PATH based on TMDB metadata.

    Examples:
      bangumi-renamer ~/Videos/anime
      bangumi-renamer ~/Videos/anime --apply --yes
      bangumi-renamer ~/Videos/anime --tmdb-id 209867 --plain

    Support:
      See README.md in this repository and open an issue there if matching looks wrong.
    """
    del version

    stdout_console = _make_console(no_color=no_color)
    stderr_console = _make_console(stderr=True, no_color=no_color)
    try:
        if plain and json_output:
            stderr_console.print("[red]Choose either --plain or --json, not both.[/]")
            raise typer.Exit(code=2)

        output_mode = (
            "json"
            if json_output
            else "plain" if plain or not sys.stdout.isatty() else "table"
        )
        files = scan(path)
        if not files:
            stderr_console.print("[yellow]No video files or supported subtitle files found.[/]")
            raise typer.Exit(code=0)

        client = TmdbClient(lang=lang)
        try:
            forced = force_match(tmdb_id, client=client) if tmdb_id is not None else None
            if forced is not None and verbose:
                stderr_console.print(
                    f"[dim]Forcing match: {forced.name} (tmdb_id={forced.tmdb_id})[/]"
                )

            root = path if path.is_dir() else path.parent
            plan = build_plan(
                files=files,
                client=client,
                forced=forced,
                on_conflict=on_conflict.value,
                verbose=verbose,
            )
        finally:
            client.close()

        rows = _build_rows(plan)
        renames: list[tuple[Path, Path]] = []
        history_path: Path | None = None
        applied = False

        if output_mode != "json":
            _emit_plan(rows, stdout_console=stdout_console, output_mode=output_mode)

        if not apply:
            stderr_console.print("[dim]Dry-run only. Nothing was renamed.[/]")
            if output_mode == "json":
                _write_json(
                    stdout_console,
                    _json_payload(
                        path=path,
                        rows=rows,
                        apply_requested=False,
                        applied=False,
                        renames=[],
                        history_path=None,
                    )
                )
            else:
                stderr_console.print(f"[dim]{_suggest_apply(path)}[/]")
            raise typer.Exit(code=0)

        to_apply: list[PlanItem] = [
            item for item in plan if item.status == "OK" and item.target is not None
        ]
        if not to_apply:
            stderr_console.print("[yellow]Nothing to apply.[/]")
            if output_mode == "json":
                _write_json(
                    stdout_console,
                    _json_payload(
                        path=path,
                        rows=rows,
                        apply_requested=True,
                        applied=False,
                        renames=[],
                        history_path=None,
                    )
                )
            raise typer.Exit(code=0)

        if not yes:
            if no_input or not sys.stdin.isatty():
                stderr_console.print(
                    "[red]Refusing to prompt in non-interactive mode. "
                    "Re-run with --yes to apply or omit --apply.[/]"
                )
                raise typer.Exit(code=2)
            confirmed = typer.confirm(f"Rename {len(to_apply)} file(s)?", default=False)
            if not confirmed:
                stderr_console.print("[yellow]Aborted.[/]")
                raise typer.Exit(code=1)

        renames, history_path = apply_plan(to_apply, root=root)
        applied = bool(renames)
        if output_mode == "json":
            _write_json(
                stdout_console,
                _json_payload(
                    path=path,
                    rows=rows,
                    apply_requested=True,
                    applied=applied,
                    renames=renames,
                    history_path=history_path,
                )
            )

        if renames and history_path is not None:
            stderr_console.print(
                f"[green]Renamed {len(renames)} file(s).[/] History: {history_path}"
            )
        else:
            stderr_console.print("[yellow]No files needed renaming.[/]")
    except typer.Exit:
        raise
    except (click.Abort, KeyboardInterrupt) as exc:
        stderr_console.print("[yellow]Interrupted.[/]")
        raise typer.Exit(code=130) from exc
    except (MatchError, TmdbError) as exc:
        stderr_console.print(f"[red]{exc}[/]")
        if "TMDB_API_KEY" in str(exc):
            stderr_console.print(
                "[dim]Set TMDB_API_KEY or configure the key in the GUI settings first.[/]"
            )
        else:
            stderr_console.print(
                "[dim]Check the TMDB id, API key, or network connection. "
                "Re-run with --debug for a traceback.[/]"
            )
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        if debug or os.environ.get("DEBUG") == "1":
            raise
        stderr_console.print(f"[red]Unexpected error: {exc}[/]")
        stderr_console.print("[dim]Re-run with --debug for a traceback.[/]")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
