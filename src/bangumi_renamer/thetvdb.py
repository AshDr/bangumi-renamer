"""TheTVDB v4 client with automatic bearer-token management."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .cache import JsonCache
from .tmdb import Episode, TmdbError, TvSearchResult

THETVDB_BASE_URL = "https://api4.thetvdb.com/v4"

_LANGUAGE_CODES = {
    "en": "eng",
    "en-us": "eng",
    "ja": "jpn",
    "ja-jp": "jpn",
    "zh": "zho",
    "zh-cn": "zho",
    "zh-hans": "zho",
    "zh-hant": "zho",
    "zh-tw": "zho",
}


class TheTvdbError(TmdbError):
    """Raised for TheTVDB authentication, transport, and response errors."""


class TheTvdbClient:
    """Fetch series and official-season metadata from TheTVDB v4."""

    provider_name = "TheTVDB"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        pin: str | None = None,
        lang: str = "en-US",
        cache: JsonCache | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("THETVDB_API_KEY")
        if not self.api_key:
            raise TheTvdbError(
                "THETVDB_API_KEY is not set (configure it in desktop settings or the environment)."
            )
        self.pin = pin if pin is not None else os.environ.get("THETVDB_PIN", "")
        self.lang = _language_code(lang)
        self.cache = cache or JsonCache()
        self._client = client or httpx.Client(base_url=THETVDB_BASE_URL, timeout=10.0)
        self._token: str | None = None

    def _authenticate(self) -> str:
        payload = {"apikey": self.api_key}
        if self.pin:
            payload["pin"] = self.pin
        try:
            response = self._client.post("/login", json=payload)
        except httpx.HTTPError as exc:
            raise TheTvdbError(f"TheTVDB authentication transport error: {exc}") from exc
        if response.status_code >= 400:
            raise TheTvdbError(
                f"TheTVDB authentication failed ({response.status_code}): {response.text[:200]}"
            )
        token = str((response.json().get("data") or {}).get("token") or "").strip()
        if not token:
            raise TheTvdbError("TheTVDB authentication response did not include a token.")
        self._token = token
        return token

    def _get(self, path: str, params: dict[str, Any], *, bucket: str) -> Any:
        cache_key = f"{path}?{sorted(params.items())}"
        cached = self.cache.get(bucket, cache_key)
        if cached is not None:
            return cached

        for attempt in range(2):
            token = self._token or self._authenticate()
            try:
                response = self._client.get(
                    path,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.HTTPError as exc:
                raise TheTvdbError(f"TheTVDB transport error for {path}: {exc}") from exc
            if response.status_code != 401 or attempt == 1:
                break
            self._token = None

        if response.status_code >= 400:
            raise TheTvdbError(
                f"TheTVDB {response.status_code} for {path}: {response.text[:200]}"
            )
        data = response.json()
        self.cache.set(bucket, cache_key, data)
        return data

    def search_tv(self, query: str, *, year: int | None = None) -> list[TvSearchResult]:
        params: dict[str, Any] = {
            "query": query,
            "type": "series",
            "lang": self.lang,
        }
        if year is not None:
            params["year"] = year
        payload = self._get("/search", params, bucket="thetvdb_search")
        return [_parse_search_hit(item) for item in payload.get("data", [])]

    def get_tv(self, tv_id: int) -> dict[str, Any]:
        payload = self._get(
            f"/series/{tv_id}/extended",
            {"meta": "translations"},
            bucket="thetvdb_series",
        )
        data = payload.get("data") or {}
        seasons = data.get("seasons") or []
        official = [season for season in seasons if _is_official_season(season)]
        selected = official or seasons
        return {
            "id": int(data.get("id", tv_id)),
            "name": str(data.get("name") or "").strip(),
            "original_name": str(data.get("originalName") or "").strip(),
            "seasons": [
                {"season_number": int(season.get("number", -1))}
                for season in selected
                if season.get("number") is not None
            ],
        }

    def get_season(self, tv_id: int, season: int) -> list[Episode]:
        page = 0
        episodes: list[Episode] = []
        while True:
            payload = self._get(
                f"/series/{tv_id}/episodes/official/{self.lang}",
                {"page": page, "season": season},
                bucket="thetvdb_season",
            )
            data = payload.get("data") or {}
            episodes.extend(
                Episode(
                    season=int(item.get("seasonNumber", season)),
                    number=int(item["number"]),
                    name=str(item.get("name") or "").strip(),
                )
                for item in data.get("episodes", [])
                if item.get("number") is not None
                and int(item.get("seasonNumber", season)) == season
            )
            if not (payload.get("links") or {}).get("next"):
                break
            page += 1

        if not episodes:
            raise TheTvdbError(f"season {season} not found on TheTVDB for series {tv_id}")
        return episodes

    def test_connection(self) -> None:
        """Verify network access and credentials by requesting a fresh access token."""
        self._authenticate()

    def close(self) -> None:
        self._client.close()


def _language_code(language: str) -> str:
    normalized = language.strip().lower()
    return _LANGUAGE_CODES.get(normalized, normalized or "eng")


def _parse_search_hit(item: dict[str, Any]) -> TvSearchResult:
    aliases = item.get("aliases") or []
    alias = next((value for value in aliases if isinstance(value, str) and value.strip()), "")
    first_air = str(item.get("first_air_time") or item.get("firstAired") or "")[:4]
    try:
        first_air_year = int(first_air) if first_air else None
    except ValueError:
        first_air_year = None
    return TvSearchResult(
        tmdb_id=int(item.get("tvdb_id") or item["id"]),
        name=str(item.get("name") or "").strip(),
        original_name=alias.strip(),
        first_air_year=first_air_year,
        overview=str(item.get("overview") or "").strip(),
    )


def _is_official_season(season: dict[str, Any]) -> bool:
    season_type = season.get("type") or {}
    values = {
        str(season_type.get("type") or "").lower(),
        str(season_type.get("name") or "").lower(),
    }
    return "official" in values
