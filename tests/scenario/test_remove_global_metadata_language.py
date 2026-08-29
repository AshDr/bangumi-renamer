from __future__ import annotations

import json
from pathlib import Path

from bangumi_renamer import desktop_bridge


def _isolate_settings(tmp_path: Path, monkeypatch) -> Path:
    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    monkeypatch.delenv("THETVDB_API_KEY", raising=False)
    return config_path


def test_legacy_metadata_language_is_not_returned_or_persisted(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = _isolate_settings(tmp_path, monkeypatch)
    config_path.write_text(
        json.dumps({"language": "ja-JP", "ui_language": "zh-CN"}),
        encoding="utf-8",
    )

    assert "language" not in desktop_bridge.load_settings()

    desktop_bridge.save_settings({"theme": "dark"})
    assert "language" not in json.loads(config_path.read_text(encoding="utf-8"))


def test_client_uses_explicit_workspace_language_instead_of_legacy_setting(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = _isolate_settings(tmp_path, monkeypatch)
    config_path.write_text(
        json.dumps(
            {
                "metadata_provider": "tmdb",
                "tmdb_api_key": "test-key",
                "language": "ja-JP",
            }
        ),
        encoding="utf-8",
    )

    explicit = desktop_bridge._make_client(
        {"metadata_provider": "tmdb", "language": "zh-CN"}
    )
    fallback = desktop_bridge._make_client({"metadata_provider": "tmdb"})
    try:
        assert explicit.lang == "zh-CN"
        assert fallback.lang == "en-US"
    finally:
        explicit.close()
        fallback.close()
