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
        {
            "metadata_provider": "tmdb",
            "api_key": "secret",
            "conflict_policy": "skip",
        }
    )

    assert settings == {
        "metadata_provider": "tmdb",
        "ui_language": "en-US",
        "conflict_policy": "skip",
        "theme": "system",
        "has_api_key": True,
        "api_key_from_environment": False,
        "has_thetvdb_api_key": False,
        "thetvdb_api_key_from_environment": False,
        "has_thetvdb_pin": False,
        "thetvdb_pin_from_environment": False,
        "has_tmdb_api_key": True,
        "tmdb_api_key_from_environment": False,
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


def test_apply_rejects_changed_compound_subtitle_extension(tmp_path: Path) -> None:
    source = tmp_path / "Episode 01.chs.ass"
    source.touch()

    with pytest.raises(ValueError, match="preserve the source extension"):
        desktop_bridge.apply_items(
            {
                "root": str(tmp_path),
                "items": [
                    {
                        "source": str(source),
                        "target": str(tmp_path / "Episode S01E01.cht.ass"),
                        "status": "OK",
                    }
                ],
            }
        )


def test_dispatch_rejects_unknown_command() -> None:
    with pytest.raises(ValueError, match="Unsupported desktop command"):
        desktop_bridge.dispatch("system.shell", {})


@pytest.mark.parametrize(
    ("provider", "payload", "client_name", "expected_credentials"),
    [
        ("tmdb", {"tmdb_api_key": "new-tmdb-key"}, "TmdbClient", ("new-tmdb-key", None)),
        (
            "thetvdb",
            {"thetvdb_api_key": "new-tvdb-key", "thetvdb_pin": "1234"},
            "TheTvdbClient",
            ("new-tvdb-key", "1234"),
        ),
    ],
)
def test_connection_uses_unsaved_credentials_and_closes_client(
    provider: str,
    payload: dict[str, str],
    client_name: str,
    expected_credentials: tuple[str, str | None],
    monkeypatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeClient:
        def __init__(self, api_key: str, *, pin: str | None = None, **_kwargs) -> None:
            calls.append(("credentials", (api_key, pin)))

        def test_connection(self) -> None:
            calls.append(("test", None))

        def close(self) -> None:
            calls.append(("close", None))

    monkeypatch.setattr(desktop_bridge, client_name, FakeClient)

    result = desktop_bridge.dispatch(
        "settings.test_connection",
        {"metadata_provider": provider, **payload},
    )

    assert result == {"provider": provider, "connected": True}
    assert calls == [
        ("credentials", expected_credentials),
        ("test", None),
        ("close", None),
    ]


def test_connection_falls_back_to_saved_credential(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text('{"tmdb_api_key":"saved-key"}', encoding="utf-8")
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    received_keys: list[str] = []

    class FakeTmdbClient:
        def __init__(self, api_key: str, **_kwargs) -> None:
            received_keys.append(api_key)

        def test_connection(self) -> None:
            pass

        def close(self) -> None:
            pass

    monkeypatch.setattr(desktop_bridge, "TmdbClient", FakeTmdbClient)

    desktop_bridge.test_provider_connection({"metadata_provider": "tmdb"})

    assert received_keys == ["saved-key"]
