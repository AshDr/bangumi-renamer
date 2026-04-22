"""Typed wrapper around ``QSettings`` for user-facing preferences.

Keys are kept in one place so the rest of the GUI doesn't spell them wrong.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QSettings

ORG = "MiniFileBot"
APP = "app"


def _qs() -> QSettings:
    return QSettings(ORG, APP)


def get_api_key() -> str:
    """Return the TMDB API key from the environment first, then QSettings."""
    env = os.environ.get("TMDB_API_KEY", "").strip()
    if env:
        return env
    return str(_qs().value("api_key", "") or "")


def set_api_key(key: str) -> None:
    _qs().setValue("api_key", key.strip())


def get_lang() -> str:
    return str(_qs().value("lang", "en-US") or "en-US")


def set_lang(lang: str) -> None:
    _qs().setValue("lang", lang)


def get_on_conflict() -> str:
    return str(_qs().value("on_conflict", "suffix") or "suffix")


def set_on_conflict(policy: str) -> None:
    _qs().setValue("on_conflict", policy)
