"""Rich presentation of rename plans."""

from __future__ import annotations

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


def render_summary(rows: list[PlanRow], console: Console) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    parts = [f"[{STATUS_STYLES.get(s, 'white')}]{s}: {n}[/]" for s, n in sorted(counts.items())]
    console.print("  ".join(parts) if parts else "no files")
