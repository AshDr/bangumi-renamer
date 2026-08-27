from __future__ import annotations

import json
from pathlib import Path

from bangumi_renamer import desktop_bridge


def configure_settings_path(tmp_path: Path, monkeypatch) -> Path:
    """Point desktop settings operations at an isolated test file."""
    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    return config_path


def test_dark_theme_round_trips_through_desktop_settings(tmp_path: Path, monkeypatch) -> None:
    config_path = configure_settings_path(tmp_path, monkeypatch)

    settings = desktop_bridge.save_settings({"theme": "dark"})

    assert settings["theme"] == "dark"
    assert json.loads(config_path.read_text(encoding="utf-8"))["theme"] == "dark"


def test_invalid_theme_falls_back_to_system(tmp_path: Path, monkeypatch) -> None:
    config_path = configure_settings_path(tmp_path, monkeypatch)
    config_path.write_text(json.dumps({"theme": "neon"}), encoding="utf-8")

    assert desktop_bridge.load_settings()["theme"] == "system"
    assert desktop_bridge.save_settings({"theme": "sepia"})["theme"] == "system"
