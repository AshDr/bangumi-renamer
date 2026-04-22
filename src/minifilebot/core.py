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
    season_cache: dict[tuple[int, int], dict[int, Episode]] = {}
    match_cache: dict[str, MatchResult | MatchError] = {}
    plan: list[PlanItem] = []
    planned_targets: set[Path] = set()

    total = len(files)
    for idx, source in enumerate(files, 1):
        if progress_cb is not None:
            progress_cb(idx, total, source)

        try:
            parsed = parse(source)
        except ParseError as exc:
            plan.append(
                PlanItem(source, None, None, None, "unparsed", detail=str(exc) if verbose else "")
            )
            continue

        if forced is not None:
            match_result: MatchResult = forced
        else:
            cached = match_cache.get(parsed.title)
            if isinstance(cached, MatchResult):
                match_result = cached
            elif isinstance(cached, MatchError):
                plan.append(PlanItem(source, parsed, None, None, "no match", detail=str(cached)))
                continue
            else:
                try:
                    match_result = match(parsed.title, client=client)
                except MatchError as exc:
                    match_cache[parsed.title] = exc
                    plan.append(
                        PlanItem(source, parsed, None, None, "no match", detail=str(exc))
                    )
                    continue
                match_cache[parsed.title] = match_result

        key = (match_result.tmdb_id, parsed.season)
        if key not in season_cache:
            try:
                episodes = client.get_season(match_result.tmdb_id, parsed.season)
            except TmdbError:
                detail = explain_season_lookup_failure(
                    client, match_result.tmdb_id, match_result.name, parsed.season
                )
                plan.append(
                    PlanItem(source, parsed, match_result, None, "no season", detail=detail)
                )
                continue
            season_cache[key] = {ep.number: ep for ep in episodes}

        ep = season_cache[key].get(parsed.episode)
        episode_title = ep.name if ep else ""

        new_name = build_new_name(
            series=match_result.name,
            season=parsed.season,
            episode=parsed.episode,
            episode_title=episode_title,
            extension=parsed.extension,
        )
        target = source.with_name(new_name)

        if target == source:
            plan.append(PlanItem(source, parsed, match_result, target, "OK", detail="no-op"))
            continue

        resolved = resolve_conflict(target, on_conflict=on_conflict)
        if resolved is None or resolved in planned_targets:
            plan.append(
                PlanItem(
                    source, parsed, match_result, target, "conflict",
                    detail=f"target exists: {target.name}",
                )
            )
            continue
        planned_targets.add(resolved)
        plan.append(PlanItem(source, parsed, match_result, resolved, "OK"))

    return plan


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
