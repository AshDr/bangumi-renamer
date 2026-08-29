"""Shared interface implemented by metadata providers."""

from __future__ import annotations

from typing import Any, Protocol

from .tmdb import Episode, TvSearchResult


class MetadataClient(Protocol):
    """Provider contract consumed by matching and plan generation."""

    provider_name: str

    def search_tv(self, query: str, *, year: int | None = None) -> list[TvSearchResult]: ...

    def get_tv(self, tv_id: int) -> dict[str, Any]: ...

    def get_season(self, tv_id: int, season: int) -> list[Episode]: ...

    def close(self) -> None: ...
