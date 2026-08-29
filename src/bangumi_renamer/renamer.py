"""Turn (ParsedFile, series_name, episode_title) into a safe target filename."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Windows reserves these; also strip controls. We keep the set small and well-known.
_ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE_RE = re.compile(r"\s+")

# Leave headroom for the extension + dot when clamping to 255 bytes.
_MAX_STEM_BYTES = 240


def sanitize_component(name: str) -> str:
    """Make ``name`` safe to use as one filename component on any mainstream FS."""
    cleaned = unicodedata.normalize("NFC", name)
    cleaned = _ILLEGAL_CHARS_RE.sub(" ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    cleaned = cleaned.rstrip(". ")
    return cleaned or "_"


def build_new_name(
    *,
    series: str,
    season: int,
    episode: int,
    episode_title: str,
    extension: str,
) -> str:
    """Produce ``{series}-S{season:02}E{episode:02}.{ext}``."""
    series_component = sanitize_component(series).rstrip("-") or "_"
    stem = f"{series_component}-S{season:02d}E{episode:02d}"
    stem_bytes = stem.encode("utf-8")
    if len(stem_bytes) > _MAX_STEM_BYTES:
        # Truncate on a char boundary, not a byte boundary.
        while len(stem.encode("utf-8")) > _MAX_STEM_BYTES:
            stem = stem[:-1]
        stem = stem.rstrip(". ")
    ext = extension.lstrip(".").lower() or "mkv"
    return f"{stem}.{ext}"


def resolve_conflict(
    target: Path,
    *,
    on_conflict: str = "suffix",
    extension: str | None = None,
) -> Path | None:
    """Return the final target path, or None if we should skip.

    ``on_conflict`` is one of ``skip``, ``suffix``, ``overwrite``.
    """
    if not target.exists():
        return target
    if on_conflict == "overwrite":
        return target
    if on_conflict == "skip":
        return None
    # Keep language/disposition tags inside compound subtitle extensions.
    compound_suffix = f".{extension.lstrip('.')}" if extension else target.suffix
    if not target.name.lower().endswith(compound_suffix.lower()):
        compound_suffix = target.suffix
    stem = target.name[: -len(compound_suffix)]
    for i in range(1, 1000):
        candidate = target.with_name(f"{stem} ({i}){compound_suffix}")
        if not candidate.exists():
            return candidate
    return None
