from __future__ import annotations

from pathlib import Path

import pytest

from bangumi_renamer import desktop_bridge


def test_settings_round_trip_without_returning_secret(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)

    settings = desktop_bridge.save_settings(
        {"api_key": "secret", "language": "zh-CN", "conflict_policy": "skip"}
    )

    assert settings == {
        "ui_language": "en-US",
        "language": "zh-CN",
        "conflict_policy": "skip",
        "theme": "system",
        "has_api_key": True,
        "api_key_from_environment": False,
    }
    assert "secret" not in str(settings)
    assert config_path.stat().st_mode & 0o777 == 0o600


def test_apply_rejects_target_outside_selected_root(tmp_path: Path) -> None:
    root = tmp_path / "shows"
    root.mkdir()
    source = root / "Episode 01.mkv"
    source.touch()

    with pytest.raises(ValueError, match="source directory"):
        desktop_bridge.apply_items(
            {
                "root": str(root),
                "items": [
                    {
                        "source": str(source),
                        "target": str(tmp_path / "Episode S01E01.mkv"),
                        "status": "OK",
                    }
                ],
            }
        )


def test_dispatch_rejects_unknown_command() -> None:
    with pytest.raises(ValueError, match="Unsupported desktop command"):
        desktop_bridge.dispatch("system.shell", {})
