"""Wraps anitopy into a regular ParsedFile dataclass usable by the rest of the pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import anitopy

_WHITESPACE_RE = re.compile(r"\s+")
_DECIMAL_NUMBER = r"[0-9０-９]"
# Fallback markers are anchored so numbers inside a title are not treated as episodes.
_EPISODE_MARKER_PATTERNS = (
    re.compile(
        rf"^(?P<title>.+?)\s*第\s*(?P<episode>{_DECIMAL_NUMBER}{{1,4}})\s*[集话話]\s*$"
    ),
    re.compile(
        rf"^(?P<title>.+?)\s+(?:Episode|Ep\.?)\s*"
        rf"(?P<episode>{_DECIMAL_NUMBER}{{1,4}})\s*$",
        re.IGNORECASE,
    ),
)
_SEASON_MARKER_PATTERNS = (
    re.compile(
        rf"^(?P<title>.+?)\s*第\s*(?P<season>{_DECIMAL_NUMBER}{{1,3}})\s*[季期]\s*$"
    ),
    re.compile(
        rf"^(?P<title>.+?)\s+Season\s*(?P<season>{_DECIMAL_NUMBER}{{1,3}})\s*$",
        re.IGNORECASE,
    ),
)


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
    year: int | None = None


class ParseError(ValueError):
    """Raised when anitopy output is missing the fields minifilebot needs."""


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _extract_fallback_markers(title: str) -> tuple[str, int | None, int | None]:
    """Extract multilingual season and episode suffixes missed by anitopy."""
    for episode_pattern in _EPISODE_MARKER_PATTERNS:
        episode_match = episode_pattern.fullmatch(title)
        if episode_match is None:
            continue

        clean_title = episode_match.group("title").rstrip(" ._-")
        episode = _to_int(episode_match.group("episode"))
        season: int | None = None

        for season_pattern in _SEASON_MARKER_PATTERNS:
            season_match = season_pattern.fullmatch(clean_title)
            if season_match is None:
                continue
            clean_title = season_match.group("title").rstrip(" ._-")
            season = _to_int(season_match.group("season"))
            break

        return _normalize_title(clean_title), season, episode

    return title, None, None


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
    year = _to_int(raw.get("anime_year"))
    fallback_season: int | None = None
    if title and episode is None:
        title, fallback_season, episode = _extract_fallback_markers(title)
    if not title or episode is None:
        raise ParseError(f"anitopy could not extract title+episode from {p.name!r}")

    anime_type = (raw.get("anime_type") or "").upper()
    is_special = anime_type in {"SP", "SPECIAL", "OVA", "ONA", "OAV"}

    season = _to_int(raw.get("anime_season"))
    if season is None:
        # Specials land in season 0 by TMDB convention; everything else defaults to S1.
        season = fallback_season if fallback_season is not None else 0 if is_special else 1

    return ParsedFile(
        source=p,
        title=title,
        season=season,
        episode=episode,
        is_special=is_special,
        release_group=raw.get("release_group"),
        extension=(raw.get("file_extension") or p.suffix.lstrip(".")).lower(),
        year=year,
    )
