"""Presentation helpers for rename plans."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass(frozen=True, slots=True)
class PlanRow:
    source: Path
    target_name: str | None  # None when status != OK
    status: str  # "OK", "unparsed", "no match", "conflict", "error"
    detail: str = ""


STATUS_STYLES = {
    "OK": "green",
    "unparsed": "yellow",
    "no match": "yellow",
    "no season": "yellow",
    "conflict": "yellow",
    "error": "red",
}


def summarize_rows(rows: list[PlanRow]) -> dict[str, int]:
    """Return per-status counts for ``rows``."""
    return dict(sorted(Counter(row.status for row in rows).items()))


def render_table(rows: list[PlanRow], console: Console) -> None:
    table = Table(show_lines=False, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Source")
    table.add_column("-> Target")
    table.add_column("Status")

    for idx, row in enumerate(rows, 1):
        status_style = STATUS_STYLES.get(row.status, "white")
        target_text = row.target_name or f"[{status_style}]{row.detail or '-'}[/]"
        table.add_row(
            str(idx),
            row.source.name,
            target_text,
            f"[{status_style}]{row.status}[/]",
        )
    console.print(table)


def render_plain(rows: list[PlanRow], console: Console) -> None:
    """Render a stable tab-separated format for scripts."""
    console.file.write("source\ttarget\tstatus\tdetail\n")
    for row in rows:
        console.file.write(
            "\t".join(
                [row.source.name, row.target_name or "", row.status, row.detail]
            )
            + "\n"
        )


def render_summary(rows: list[PlanRow], console: Console) -> None:
    counts = summarize_rows(rows)
    parts = [f"[{STATUS_STYLES.get(s, 'white')}]{s}: {n}[/]" for s, n in sorted(counts.items())]
    console.print("  ".join(parts) if parts else "no files")
