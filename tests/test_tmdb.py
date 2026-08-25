"""TmdbClient tests using respx to mock the TMDB HTTP layer."""

from __future__ import annotations

import httpx
import pytest
import respx

from minifilebot.cache import JsonCache
from minifilebot.tmdb import TMDB_BASE_URL, Episode, TmdbClient, TmdbError, TvSearchResult


@respx.mock
def test_search_tv_returns_parsed_results(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 209867,
                        "name": "Frieren: Beyond Journey's End",
                        "original_name": "\u846c\u9001\u306e\u30d5\u30ea\u30fc\u30ec\u30f3",
                        "first_air_date": "2023-09-29",
                        "overview": "...",
                    }
                ]
            },
        )
    )
    results = tmdb_client.search_tv("Frieren")
    assert results == [
        TvSearchResult(
            tmdb_id=209867,
            name="Frieren: Beyond Journey's End",
            original_name="\u846c\u9001\u306e\u30d5\u30ea\u30fc\u30ec\u30f3",
            first_air_year=2023,
            overview="...",
        )
    ]


@respx.mock
def test_search_tv_uses_cache_on_second_call(tmdb_client: TmdbClient) -> None:
    route = respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    tmdb_client.search_tv("Frieren")
    tmdb_client.search_tv("Frieren")
    assert route.call_count == 1


@respx.mock
def test_search_tv_passes_year_filter(tmdb_client: TmdbClient) -> None:
    route = respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    tmdb_client.search_tv("Frieren", year=2023)
    assert route.calls.last.request.url.params["first_air_date_year"] == "2023"


@respx.mock
def test_get_tv_returns_raw_payload(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/tv/209867").mock(
        return_value=httpx.Response(
            200,
            json={"id": 209867, "name": "Frieren: Beyond Journey's End", "number_of_seasons": 1},
        )
    )
    data = tmdb_client.get_tv(209867)
    assert data["name"] == "Frieren: Beyond Journey's End"


@respx.mock
def test_get_season_parses_episodes(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/tv/209867/season/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "episodes": [
                    {"season_number": 1, "episode_number": 1, "name": "The Journey's End"},
                    {"season_number": 1, "episode_number": 2, "name": "It Didn't Have To Be Magic"},
                ]
            },
        )
    )
    episodes = tmdb_client.get_season(209867, 1)
    assert episodes == [
        Episode(season=1, number=1, name="The Journey's End"),
        Episode(season=1, number=2, name="It Didn't Have To Be Magic"),
    ]


@respx.mock
def test_non_2xx_raises(tmdb_client: TmdbClient) -> None:
    respx.get(f"{TMDB_BASE_URL}/tv/999999999").mock(
        return_value=httpx.Response(404, json={"status_message": "Not Found"})
    )
    with pytest.raises(TmdbError):
        tmdb_client.get_tv(999999999)


def test_missing_api_key_raises(tmp_path, monkeypatch) -> None:
    # Isolate the constructor from any real credential in the developer shell.
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    cache = JsonCache(root=tmp_path, ttl=3600)
    with pytest.raises(TmdbError):
        TmdbClient(api_key=None, cache=cache)
