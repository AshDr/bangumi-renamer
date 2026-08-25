"""Tiny JSON file cache with TTL.

Used only for TMDB responses. Not thread-safe, but the CLI runs a single
process so that is fine. Cache directory lives under platformdirs' user cache
(e.g. ``~/Library/Caches/bangumi-renamer`` on macOS).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _default_cache_root() -> Path:
    return Path(user_cache_dir("bangumi-renamer"))


class JsonCache:
    """Bucketed JSON cache keyed by a freeform string."""

    def __init__(self, root: Path | None = None, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        self.root = root or _default_cache_root()
        self.ttl = ttl

    def _path(self, bucket: str, key: str) -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self.root / bucket / f"{digest}.json"

    def get(self, bucket: str, key: str) -> Any | None:
        path = self._path(bucket, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() - payload.get("stored_at", 0) > self.ttl:
            return None
        return payload.get("value")

    def set(self, bucket: str, key: str, value: Any) -> None:
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"stored_at": time.time(), "value": value}, ensure_ascii=False),
            encoding="utf-8",
        )
