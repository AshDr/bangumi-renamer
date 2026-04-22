"""JsonCache TTL + bucketing."""

from __future__ import annotations

import time
from pathlib import Path

from minifilebot.cache import JsonCache


def test_set_and_get_roundtrip(tmp_path: Path) -> None:
    cache = JsonCache(root=tmp_path, ttl=3600)
    cache.set("search_tv", "Frieren", {"results": [1, 2, 3]})
    assert cache.get("search_tv", "Frieren") == {"results": [1, 2, 3]}


def test_miss_returns_none(tmp_path: Path) -> None:
    cache = JsonCache(root=tmp_path, ttl=3600)
    assert cache.get("search_tv", "never-stored") is None


def test_ttl_expiry(tmp_path: Path) -> None:
    cache = JsonCache(root=tmp_path, ttl=0)
    cache.set("tv", "209867", {"name": "Frieren"})
    time.sleep(0.01)
    assert cache.get("tv", "209867") is None


def test_buckets_are_isolated(tmp_path: Path) -> None:
    cache = JsonCache(root=tmp_path, ttl=3600)
    cache.set("search_tv", "key", "search-value")
    cache.set("tv", "key", "tv-value")
    assert cache.get("search_tv", "key") == "search-value"
    assert cache.get("tv", "key") == "tv-value"
