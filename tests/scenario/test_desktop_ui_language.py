from __future__ import annotations

import json
from pathlib import Path

from bangumi_renamer import desktop_bridge


def _isolate_settings(tmp_path: Path, monkeypatch) -> Path:
    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    return config_path


def test_ui_language_round_trips_without_global_metadata_language(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = _isolate_settings(tmp_path, monkeypatch)

    settings = desktop_bridge.save_settings(
        {"ui_language": "ja-JP", "conflict_policy": "suffix"}
    )

    assert settings["ui_language"] == "ja-JP"
    assert "language" not in settings
    assert json.loads(config_path.read_text(encoding="utf-8"))["ui_language"] == "ja-JP"


def test_invalid_ui_language_falls_back_to_english(tmp_path: Path, monkeypatch) -> None:
    config_path = _isolate_settings(tmp_path, monkeypatch)
    config_path.write_text('{"ui_language": "fr-FR"}', encoding="utf-8")

    assert desktop_bridge.load_settings()["ui_language"] == "en-US"
    assert desktop_bridge.save_settings({"ui_language": "invalid"})["ui_language"] == "en-US"
