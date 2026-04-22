"""Persist each --apply run so a future `undo` can find it."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def record_apply(root: Path, renames: list[tuple[Path, Path]]) -> Path:
    """Write a JSON file under ``<root>/.minifilebot/history/<ts>.json``.

    Returns the history file path.
    """
    history_dir = root / ".minifilebot" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    out_file = history_dir / f"{timestamp}.json"
    payload = {
        "timestamp": timestamp,
        "renames": [{"from": str(src), "to": str(dst)} for src, dst in renames],
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_file
