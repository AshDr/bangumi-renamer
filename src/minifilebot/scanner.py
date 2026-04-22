"""Discover video files to process."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

VIDEO_EXTENSIONS = frozenset({".mkv", ".mp4", ".avi", ".m4v", ".mov"})


def scan(path: Path) -> list[Path]:
    """Return video files under ``path`` (recursive if directory, [path] if file).

    Hidden files and minifilebot's own history directory are skipped.
    Results are sorted for stable output.
    """
    if path.is_file():
        return [path] if path.suffix.lower() in VIDEO_EXTENSIONS else []

    return sorted(_iter_videos(path))


def _iter_videos(root: Path) -> Iterable[Path]:
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if any(part.startswith(".") for part in candidate.relative_to(root).parts):
            continue
        yield candidate
