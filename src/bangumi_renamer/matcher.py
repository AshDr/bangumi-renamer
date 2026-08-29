"""Pick the best TV result returned by a metadata provider.

Scoring: rapidfuzz ``WRatio`` (case-insensitive) against both ``name`` and
``original_name``, take the max. ``WRatio`` is the right choice here because
it combines partial + token-based strategies, which lets short queries like
``Frieren`` match long titles like ``Frieren: Beyond Journey's End``. Year
match within +/-1 adds 15. Anything below ``MIN_CONFIDENCE`` is rejected so
callers can surface "no match" instead of silently renaming to a wrong show.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from .metadata import MetadataClient
from .tmdb import TmdbError, TvSearchResult

MIN_CONFIDENCE = 75.0
YEAR_BONUS = 15.0


class MatchError(RuntimeError):
    """Raised when no candidate clears the confidence threshold."""


@dataclass(frozen=True, slots=True)
class MatchResult:
    tmdb_id: int
    name: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    """A provider TV search hit annotated with our confidence score.

    Used by the GUI's "Pick different match" dialog, where the user needs to
    see every candidate — not just the winner — to pick the right one.
    """

    tmdb_id: int
    name: str
    original_name: str
    first_air_year: int | None
    overview: str
    confidence: float
    reason: str


def _score_candidate(
    title: str, candidate: TvSearchResult, hint_year: int | None
) -> tuple[float, str]:
    q = title.lower()
    a = fuzz.WRatio(q, candidate.name.lower()) if candidate.name else 0.0
    b = fuzz.WRatio(q, candidate.original_name.lower()) if candidate.original_name else 0.0
    base = max(a, b)
    reason = f"fuzzy={base:.0f}"
    if (
        hint_year is not None
        and candidate.first_air_year is not None
        and abs(candidate.first_air_year - hint_year) <= 1
    ):
        base += YEAR_BONUS
        reason += f" +year({candidate.first_air_year})"
    return base, reason


def search_candidates(
    title: str,
    *,
    client: MetadataClient,
    hint_year: int | None = None,
) -> list[ScoredCandidate]:
    """Return every provider candidate for ``title``, scored and sorted descending.

    Never raises on low scores — that's the caller's policy. Returns an empty
    list when the provider has no results for the query.
    """
    hits = client.search_tv(title, year=hint_year)
    scored: list[ScoredCandidate] = []
    for hit in hits:
        score, reason = _score_candidate(title, hit, hint_year)
        scored.append(
            ScoredCandidate(
                tmdb_id=hit.tmdb_id,
                name=hit.name,
                original_name=hit.original_name,
                first_air_year=hit.first_air_year,
                overview=hit.overview,
                confidence=score,
                reason=reason,
            )
        )
    scored.sort(key=lambda c: c.confidence, reverse=True)
    return scored


def match(
    title: str,
    *,
    client: MetadataClient,
    hint_year: int | None = None,
) -> MatchResult:
    """Search the provider for `title` and pick the best candidate."""
    candidates = search_candidates(title, client=client, hint_year=hint_year)
    if not candidates:
        raise MatchError(f"{client.provider_name} returned no results for {title!r}")

    best = candidates[0]
    if best.confidence < MIN_CONFIDENCE:
        raise MatchError(
            f"best candidate {best.name!r} scored {best.confidence:.0f} < {MIN_CONFIDENCE:.0f}"
        )
    return MatchResult(
        tmdb_id=best.tmdb_id,
        name=best.name,
        confidence=best.confidence,
        reason=best.reason,
    )


def force_match(tmdb_id: int, *, client: MetadataClient) -> MatchResult:
    """Bypass fuzzy matching by validating a provider-specific series id."""
    try:
        data = client.get_tv(tmdb_id)
    except TmdbError as exc:
        if client.provider_name == "TMDB":
            raise MatchError(
                f"--tmdb-id {tmdb_id} is not a valid TMDB TV id: {exc}"
            ) from exc
        raise MatchError(
            f"{tmdb_id} is not a valid {client.provider_name} series id: {exc}"
        ) from exc
    fallback = f"tmdb:{tmdb_id}" if client.provider_name == "TMDB" else f"thetvdb:{tmdb_id}"
    name = (data.get("name") or data.get("original_name") or fallback).strip()
    return MatchResult(tmdb_id=tmdb_id, name=name, confidence=100.0, reason="manual override")
