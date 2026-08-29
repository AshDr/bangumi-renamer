"""Discover video and external subtitle files to process."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

VIDEO_EXTENSIONS = frozenset({".mkv", ".mp4", ".avi", ".m4v", ".mov"})
SUBTITLE_EXTENSIONS = frozenset(
    {".ass", ".ssa", ".srt", ".vtt", ".sub", ".idx", ".sup", ".mks"}
)
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS


def scan(path: Path) -> list[Path]:
    """Return media files under ``path`` (recursive if directory, [path] if file).

    Hidden files and Bangumi Renamer's own history directory are skipped.
    Results are sorted for stable output.
    """
    if path.is_file():
        return [path] if path.suffix.lower() in MEDIA_EXTENSIONS else []

    return sorted(_iter_media(path))


def _iter_media(root: Path) -> Iterable[Path]:
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        if any(part.startswith(".") for part in candidate.relative_to(root).parts):
            continue
        yield candidate
