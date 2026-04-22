"""Matcher tests covering scoring, year tiebreaker, and --tmdb-id override."""

from __future__ import annotations

import httpx
import pytest
import respx

from minifilebot.matcher import MatchError, force_match, match
from minifilebot.tmdb import TMDB_BASE_URL, TmdbClient


def _search_payload(*results: dict) -> dict:
    return {"results": list(results)}


@respx.mock
def test_match_picks_best_fuzzy_candidate(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_search_payload(
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
                    "overview": "",
                },
            ),
        )
    )
    result = match("Frieren", client=tmdb_client)
    assert result.tmdb_id == 209867
    assert result.confidence >= 75.0


@respx.mock
def test_match_year_breaks_ties(tmdb_client: TmdbClient) -> None:
    # Two candidates with the same name, different years. The year hint should decide.
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_search_payload(
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
    result = match("Hunter x Hunter", client=tmdb_client, hint_year=2011)
    assert result.tmdb_id == 2


@respx.mock
def test_match_rejects_below_threshold(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json=_search_payload(
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
    with pytest.raises(MatchError):
        match("Frieren", client=tmdb_client)


@respx.mock
def test_match_empty_results_raises(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    with pytest.raises(MatchError):
        match("Whatever", client=tmdb_client)


@respx.mock
def test_force_match_validates_id_and_bypasses_search(tmdb_client: TmdbClient) -> None:
    search = respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    respx.get(f"{TMDB_BASE_URL}/tv/209867").mock(
        return_value=httpx.Response(
            200, json={"id": 209867, "name": "Frieren: Beyond Journey's End"}
        )
    )
    result = force_match(209867, client=tmdb_client)
    assert result.tmdb_id == 209867
    assert result.name == "Frieren: Beyond Journey's End"
    assert result.confidence == 100.0
    assert search.call_count == 0  # no search performed


@respx.mock
def test_force_match_invalid_id_raises(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/tv/999999999").mock(
        return_value=httpx.Response(404, json={"status_message": "Not Found"})
    )
    with pytest.raises(MatchError):
        force_match(999999999, client=tmdb_client)
