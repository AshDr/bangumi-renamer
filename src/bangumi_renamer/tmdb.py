"""Thin TMDB v3 client.

Auth uses the classic v3 ``api_key`` query param (simpler to hand out and the
key readers ask TMDB for in their free tier). Responses are run through a
local JSON cache to keep repeat runs offline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from .cache import JsonCache

TMDB_BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_LANG = "en-US"


class TmdbError(RuntimeError):
    """Raised for transport errors, non-2xx responses, or missing API key."""


@dataclass(frozen=True, slots=True)
class TvSearchResult:
    tmdb_id: int
    name: str
    original_name: str
    first_air_year: int | None
    overview: str


@dataclass(frozen=True, slots=True)
class Episode:
    season: int
    number: int
    name: str


class TmdbClient:
    provider_name = "TMDB"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        lang: str = DEFAULT_LANG,
        cache: JsonCache | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")
        if not self.api_key:
            raise TmdbError("TMDB_API_KEY is not set (pass api_key= or set the env var).")
        self.lang = lang
        self.cache = cache or JsonCache()
        self._client = client or httpx.Client(base_url=TMDB_BASE_URL, timeout=10.0)

    def _get(self, path: str, params: dict[str, Any], *, bucket: str) -> Any:
        # Cache key includes path, lang, and sorted params; api_key is deliberately
        # excluded so rotated keys still reuse cached responses.
        params = {"language": self.lang, **params}
        cache_key = f"{path}?{sorted(params.items())}"
        cached = self.cache.get(bucket, cache_key)
        if cached is not None:
            return cached

        request_params = {"api_key": self.api_key, **params}
        try:
            response = self._client.get(path, params=request_params)
        except httpx.HTTPError as exc:
            raise TmdbError(f"TMDB transport error for {path}: {exc}") from exc
        if response.status_code >= 400:
            raise TmdbError(f"TMDB {response.status_code} for {path}: {response.text[:200]}")
        data = response.json()
        self.cache.set(bucket, cache_key, data)
        return data

    def search_tv(self, query: str, *, year: int | None = None) -> list[TvSearchResult]:
        params: dict[str, Any] = {"query": query, "include_adult": "false"}
        if year is not None:
            params["first_air_date_year"] = year
        data = self._get("/search/tv", params, bucket="search_tv")
        return [_parse_search_hit(item) for item in data.get("results", [])]

    def get_tv(self, tv_id: int) -> dict[str, Any]:
        return self._get(f"/tv/{tv_id}", {}, bucket="tv")

    def get_season(self, tv_id: int, season: int) -> list[Episode]:
        data = self._get(f"/tv/{tv_id}/season/{season}", {}, bucket="season")
        episodes: list[Episode] = []
        for ep in data.get("episodes", []):
            episodes.append(
                Episode(
                    season=int(ep.get("season_number", season)),
                    number=int(ep["episode_number"]),
                    name=(ep.get("name") or "").strip(),
                )
            )
        return episodes

    def test_connection(self) -> None:
        """Verify network access and credentials without reading or writing the cache."""
        try:
            response = self._client.get("/configuration", params={"api_key": self.api_key})
        except httpx.HTTPError as exc:
            raise TmdbError(f"TMDB connection test failed: {exc}") from exc
        if response.status_code >= 400:
            raise TmdbError(
                f"TMDB connection test failed ({response.status_code}): {response.text[:200]}"
            )

    def close(self) -> None:
        self._client.close()


def _parse_search_hit(item: dict[str, Any]) -> TvSearchResult:
    air = (item.get("first_air_date") or "")[:4]
    year: int | None
    try:
        year = int(air) if air else None
    except ValueError:
        year = None
    return TvSearchResult(
        tmdb_id=int(item["id"]),
        name=(item.get("name") or "").strip(),
        original_name=(item.get("original_name") or "").strip(),
        first_air_year=year,
        overview=(item.get("overview") or "").strip(),
    )
