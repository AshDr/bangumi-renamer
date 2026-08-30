from __future__ import annotations

from pathlib import Path

import httpx
import respx

from bangumi_renamer import desktop_bridge
from bangumi_renamer.cache import JsonCache
from bangumi_renamer.thetvdb import THETVDB_BASE_URL, TheTvdbClient
from bangumi_renamer.tmdb import TmdbClient


def test_new_desktop_settings_default_to_thetvdb(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", tmp_path / "settings.json")
    monkeypatch.delenv("THETVDB_API_KEY", raising=False)
    monkeypatch.delenv("THETVDB_PIN", raising=False)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)

    settings = desktop_bridge.load_settings()

    assert settings["metadata_provider"] == "thetvdb"
    assert settings["has_api_key"] is False
    assert settings["has_thetvdb_api_key"] is False
    assert settings["has_tmdb_api_key"] is False


def test_legacy_tmdb_key_is_preserved_when_switching_provider(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text('{"api_key":"legacy-secret"}', encoding="utf-8")
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("THETVDB_API_KEY", raising=False)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)

    settings = desktop_bridge.save_settings({"metadata_provider": "tmdb"})

    assert settings["metadata_provider"] == "tmdb"
    assert settings["has_api_key"] is True
    assert settings["has_tmdb_api_key"] is True
    assert "legacy-secret" not in str(settings)


def test_client_factory_routes_to_selected_provider(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text(
        '{"tmdb_api_key":"tmdb-secret","thetvdb_api_key":"tvdb-secret"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(desktop_bridge, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(desktop_bridge, "_CONFIG_PATH", config_path)
    monkeypatch.delenv("THETVDB_API_KEY", raising=False)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)

    tvdb_client = desktop_bridge._make_client(
        {"metadata_provider": "thetvdb", "language": "en-US"}
    )
    tmdb_client = desktop_bridge._make_client(
        {"metadata_provider": "tmdb", "language": "en-US"}
    )
    try:
        assert isinstance(tvdb_client, TheTvdbClient)
        assert isinstance(tmdb_client, TmdbClient)
    finally:
        tvdb_client.close()
        tmdb_client.close()


@respx.mock
def test_thetvdb_client_logs_in_searches_and_reads_official_season(tmp_path: Path) -> None:
    login = respx.post(f"{THETVDB_BASE_URL}/login").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": {"token": "jwt"}})
    )
    search = respx.get(f"{THETVDB_BASE_URL}/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": [
                    {
                        "tvdb_id": "387301",
                        "name": "呪術廻戦",
                        "aliases": ["Jujutsu Kaisen"],
                        "first_air_time": "2020-10-03",
                        "overview": "Sorcerers fight curses.",
                    }
                ],
            },
        )
    )
    episodes = respx.get(
        f"{THETVDB_BASE_URL}/series/387301/episodes/official/eng"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "episodes": [
                        {"seasonNumber": 3, "number": 1, "name": "Culling Game"},
                        {"seasonNumber": 3, "number": 2, "name": "A New Rule"},
                    ]
                },
                "links": {"next": None},
            },
        )
    )
    client = TheTvdbClient(
        api_key="tvdb-key",
        pin="subscriber-pin",
        lang="en-US",
        cache=JsonCache(root=tmp_path / "cache", ttl=3600),
    )
    try:
        results = client.search_tv("Jujutsu Kaisen")
        season = client.get_season(387301, 3)
    finally:
        client.close()

    assert results[0].tmdb_id == 387301
    assert results[0].name == "呪術廻戦"
    assert results[0].original_name == "Jujutsu Kaisen"
    assert [(episode.season, episode.number) for episode in season] == [(3, 1), (3, 2)]
    assert login.call_count == 1
    assert login.calls.last.request.content == b'{"apikey":"tvdb-key","pin":"subscriber-pin"}'
    assert search.calls.last.request.url.params["type"] == "series"
    assert episodes.calls.last.request.url.params["season"] == "3"
    assert episodes.calls.last.request.headers["Authorization"] == "Bearer jwt"


@respx.mock
def test_thetvdb_connection_test_authenticates_without_metadata_requests(tmp_path: Path) -> None:
    login = respx.post(f"{THETVDB_BASE_URL}/login").mock(
        return_value=httpx.Response(200, json={"data": {"token": "jwt"}})
    )
    client = TheTvdbClient(
        api_key="tvdb-key",
        cache=JsonCache(root=tmp_path / "cache", ttl=3600),
    )
    try:
        client.test_connection()
    finally:
        client.close()

    assert login.call_count == 1
