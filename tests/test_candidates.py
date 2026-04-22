"""Tests for matcher.search_candidates — the list-all-candidates API the GUI needs."""

from __future__ import annotations

import httpx
import respx

from minifilebot.matcher import search_candidates
from minifilebot.tmdb import TMDB_BASE_URL, TmdbClient


def _payload(*results: dict) -> dict:
    return {"results": list(results)}


@respx.mock
def test_candidates_sorted_by_confidence_desc(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_payload(
                {
                    "id": 100,
                    "name": "Totally Unrelated Show",
                    "original_name": "Totally Unrelated Show",
                    "first_air_date": "2000-01-01",
                    "overview": "",
                },
                {
                    "id": 209867,
                    "name": "Frieren: Beyond Journey's End",
                    "original_name": "Sousou no Frieren",
                    "first_air_date": "2023-09-29",
                    "overview": "A mage reflects on mortality.",
                },
            ),
        )
    )
    candidates = search_candidates("Frieren", client=tmdb_client)
    assert len(candidates) == 2
    # Best match comes first, overview preserved for the picker dialog.
    assert candidates[0].tmdb_id == 209867
    assert candidates[0].overview.startswith("A mage")
    assert candidates[0].confidence > candidates[1].confidence


@respx.mock
def test_candidates_does_not_raise_on_low_scores(tmdb_client: TmdbClient) -> None:
    """match() enforces the threshold; search_candidates MUST leave that to the caller."""
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_payload(
                {
                    "id": 1,
                    "name": "Something Completely Different",
                    "original_name": "Something Completely Different",
                    "first_air_date": "2020-01-01",
                    "overview": "",
                }
            ),
        )
    )
    candidates = search_candidates("Frieren", client=tmdb_client)
    assert len(candidates) == 1
    # The GUI will show this low-confidence row; it's user's call, not matcher's.
    assert candidates[0].confidence < 75.0


@respx.mock
def test_candidates_empty_when_tmdb_has_no_results(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    assert search_candidates("Whatever", client=tmdb_client) == []


@respx.mock
def test_candidates_year_bonus_applied(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_payload(
                {
                    "id": 1,
                    "name": "Hunter x Hunter",
                    "original_name": "Hunter x Hunter",
                    "first_air_date": "1999-10-16",
                    "overview": "",
                },
                {
                    "id": 2,
                    "name": "Hunter x Hunter",
                    "original_name": "Hunter x Hunter",
                    "first_air_date": "2011-10-02",
                    "overview": "",
                },
            ),
        )
    )
    candidates = search_candidates("Hunter x Hunter", client=tmdb_client, hint_year=2011)
    # Year hint bumps the 2011 entry above the 1999 one.
    assert candidates[0].tmdb_id == 2
    assert "+year(2011)" in candidates[0].reason
    assert candidates[1].tmdb_id == 1
