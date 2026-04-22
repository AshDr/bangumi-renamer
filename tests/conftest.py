"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from minifilebot.cache import JsonCache
from minifilebot.tmdb import TmdbClient


@pytest.fixture
def tmp_cache(tmp_path: Path) -> JsonCache:
    return JsonCache(root=tmp_path / "cache", ttl=3600)


@pytest.fixture
def tmdb_client(tmp_cache: JsonCache) -> TmdbClient:
    return TmdbClient(api_key="test-key", cache=tmp_cache)
