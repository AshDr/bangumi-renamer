"""Orchestration layer shared by the CLI and GUI front-ends.

The CLI used to embed this logic directly in ``cli.py``; factoring it out lets
the GUI run the same pipeline on a background thread without depending on
Typer or Rich.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .history import record_apply
from .matcher import MatchError, MatchResult, match
from .parser import ParsedFile, ParseError, parse
from .renamer import build_new_name, resolve_conflict
from .tmdb import Episode, TmdbClient, TmdbError

# (file_index, total_files, source_path) — GUI wires this to a progress bar.
ProgressCb = Callable[[int, int, Path], None]
SeasonCache = dict[tuple[int, int], dict[int, Episode]]
MatchCache = dict[str, MatchResult | MatchError]


@dataclass(slots=True)
class PlanItem:
    source: Path
    parsed: ParsedFile | None
    match: MatchResult | None
    target: Path | None
    status: str  # "OK" | "unparsed" | "no match" | "no season" | "conflict" | "error"
    detail: str = ""


def build_plan(
    files: list[Path],
    *,
    client: TmdbClient,
    forced: MatchResult | None,
    on_conflict: str = "suffix",
    progress_cb: ProgressCb | None = None,
    verbose: bool = False,
) -> list[PlanItem]:
    """Compute the rename plan for ``files`` without touching disk.

    Per-season TMDB fetches and per-title match results are memoised within a
    single call so a directory of one show only hits TMDB once per season.
    """
    season_cache: SeasonCache = {}
    match_cache: MatchCache = {}
    plan: list[PlanItem] = []
    planned_targets: set[Path] = set()

    total = len(files)
    for idx, source in enumerate(files, 1):
        if progress_cb is not None:
            progress_cb(idx, total, source)

        parsed = _parse_source(source, verbose=verbose)
        if isinstance(parsed, PlanItem):
            plan.append(parsed)
            continue

        match_result = _resolve_match(parsed, client=client, forced=forced, match_cache=match_cache)
        if isinstance(match_result, PlanItem):
            plan.append(match_result)
            continue

        episodes = _get_season_episodes(
            parsed,
            match_result,
            client=client,
            season_cache=season_cache,
        )
        if isinstance(episodes, PlanItem):
            plan.append(episodes)
            continue

        plan.append(
            _build_plan_item(
                source,
                parsed,
                match_result,
                episodes,
                on_conflict=on_conflict,
                planned_targets=planned_targets,
            )
        )

    return plan


def _parse_source(source: Path, *, verbose: bool) -> ParsedFile | PlanItem:
    try:
        return parse(source)
    except ParseError as exc:
        return PlanItem(
            source,
            None,
            None,
            None,
            "unparsed",
            detail=str(exc) if verbose else "",
        )


def _resolve_match(
    parsed: ParsedFile,
    *,
    client: TmdbClient,
    forced: MatchResult | None,
    match_cache: MatchCache,
) -> MatchResult | PlanItem:
    if forced is not None:
        return forced

    cached = match_cache.get(parsed.title)
    if isinstance(cached, MatchResult):
        return cached
    if isinstance(cached, MatchError):
        return PlanItem(parsed.source, parsed, None, None, "no match", detail=str(cached))

    try:
        match_result = match(parsed.title, client=client)
    except MatchError as exc:
        match_cache[parsed.title] = exc
        return PlanItem(parsed.source, parsed, None, None, "no match", detail=str(exc))

    match_cache[parsed.title] = match_result
    return match_result


def _get_season_episodes(
    parsed: ParsedFile,
    match_result: MatchResult,
    *,
    client: TmdbClient,
    season_cache: SeasonCache,
) -> dict[int, Episode] | PlanItem:
    key = (match_result.tmdb_id, parsed.season)
    episodes = season_cache.get(key)
    if episodes is not None:
        return episodes

    try:
        fetched = client.get_season(match_result.tmdb_id, parsed.season)
    except TmdbError:
        detail = explain_season_lookup_failure(
            client, match_result.tmdb_id, match_result.name, parsed.season
        )
        return PlanItem(parsed.source, parsed, match_result, None, "no season", detail=detail)

    episodes = {ep.number: ep for ep in fetched}
    season_cache[key] = episodes
    return episodes


def _build_plan_item(
    source: Path,
    parsed: ParsedFile,
    match_result: MatchResult,
    episodes: dict[int, Episode],
    *,
    on_conflict: str,
    planned_targets: set[Path],
) -> PlanItem:
    episode = episodes.get(parsed.episode)
    episode_title = episode.name if episode else ""

    new_name = build_new_name(
        series=match_result.name,
        season=parsed.season,
        episode=parsed.episode,
        episode_title=episode_title,
        extension=parsed.extension,
    )
    target = source.with_name(new_name)

    if target == source:
        return PlanItem(source, parsed, match_result, target, "OK", detail="no-op")

    resolved = resolve_conflict(
        target,
        on_conflict=on_conflict,
        extension=parsed.extension,
    )
    if resolved is None or resolved in planned_targets:
        return PlanItem(
            source,
            parsed,
            match_result,
            target,
            "conflict",
            detail=f"target exists: {target.name}",
        )

    planned_targets.add(resolved)
    return PlanItem(source, parsed, match_result, resolved, "OK")


def apply_plan(
    items: list[PlanItem],
    *,
    root: Path,
    progress_cb: ProgressCb | None = None,
) -> tuple[list[tuple[Path, Path]], Path | None]:
    """Execute renames for every OK item. Returns (renames, history_path).

    ``history_path`` is None when nothing actually moved (e.g. every OK item
    was a no-op where target == source).
    """
    renames: list[tuple[Path, Path]] = []
    total = len(items)
    for idx, item in enumerate(items, 1):
        if progress_cb is not None:
            progress_cb(idx, total, item.source)
        if item.status != "OK" or item.target is None or item.target == item.source:
            continue
        item.source.rename(item.target)
        renames.append((item.source, item.target))

    if not renames:
        return renames, None
    history_path = record_apply(root, renames)
    return renames, history_path


def explain_season_lookup_failure(
    client: TmdbClient, tmdb_id: int, series_name: str, season: int
) -> str:
    """Build a helpful detail string when /tv/{id}/season/{N} fails.

    Anime releases often tag sequels as "2nd Season" while TMDB merges them
    into a single continuous season with absolute episode numbers. Telling
    the user which seasons actually exist is more useful than the raw 404.
    """
    try:
        tv = client.get_tv(tmdb_id)
    except TmdbError:
        return f"season {season} not found on TMDB for '{series_name}'"
    available = sorted({int(s.get("season_number", -1)) for s in tv.get("seasons", [])})
    available = [n for n in available if n >= 0]
    hint = (
        " (anime 'Nth Season' tags often map to TMDB season 1 with absolute "
        "episode numbers; try --tmdb-id with the right show or re-tag the files)"
    )
    return (
        f"season {season} not found on TMDB for '{series_name}'; "
        f"available: {available}{hint}"
    )
