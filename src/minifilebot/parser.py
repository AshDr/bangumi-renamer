"""Wraps anitopy into a regular ParsedFile dataclass usable by the rest of the pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import anitopy

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_title(title: str) -> str:
    """Collapse dots/underscores to spaces; anitopy sometimes half-handles them."""
    cleaned = title.replace(".", " ").replace("_", " ")
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


@dataclass(frozen=True, slots=True)
class ParsedFile:
    """The subset of anitopy output that minifilebot cares about."""

    source: Path
    title: str
    season: int
    episode: int
    is_special: bool
    release_group: str | None
    extension: str


class ParseError(ValueError):
    """Raised when anitopy output is missing the fields minifilebot needs."""


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse(path: str | Path) -> ParsedFile:
    """Parse a single video filename.

    Raises ParseError if the filename does not yield a title + episode number.
    Missing season defaults to 1 (common for single-season shows and for anime
    where releases drop the season tag).
    """
    p = Path(path)
    try:
        raw = anitopy.parse(p.name) or {}
    except (AttributeError, TypeError, IndexError) as exc:  # anitopy has known crashers
        raise ParseError(f"anitopy crashed on {p.name!r}: {exc}") from exc

    title = _normalize_title(raw.get("anime_title") or "")
    episode = _to_int(raw.get("episode_number"))
    if not title or episode is None:
        raise ParseError(f"anitopy could not extract title+episode from {p.name!r}")

    anime_type = (raw.get("anime_type") or "").upper()
    is_special = anime_type in {"SP", "SPECIAL", "OVA", "ONA", "OAV"}

    season = _to_int(raw.get("anime_season"))
    if season is None:
        # Specials land in season 0 by TMDB convention; everything else defaults to S1.
        season = 0 if is_special else 1

    return ParsedFile(
        source=p,
        title=title,
        season=season,
        episode=episode,
        is_special=is_special,
        release_group=raw.get("release_group"),
        extension=(raw.get("file_extension") or p.suffix.lstrip(".")).lower(),
    )
