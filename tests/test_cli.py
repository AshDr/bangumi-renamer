"""End-to-end CLI tests with a fully mocked TMDB backend."""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from minifilebot.cli import app
from minifilebot.tmdb import TMDB_BASE_URL

runner = CliRunner()


def _mock_frieren() -> None:
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 209867,
                        "name": "Frieren: Beyond Journey's End",
                        "original_name": "Sousou no Frieren",
                        "first_air_date": "2023-09-29",
                        "overview": "",
                    }
                ]
            },
        )
    )
    respx.get(f"{TMDB_BASE_URL}/tv/209867/season/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "episodes": [
                    {"season_number": 1, "episode_number": 1, "name": "The Journey's End"},
                ]
            },
        )
    )


@respx.mock
def test_dry_run_previews_without_touching_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    source = tmp_path / "[SubsPlease] Frieren - 01 (1080p).mkv"
    source.touch()

    _mock_frieren()

    result = runner.invoke(app, [str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Dry-run only" in result.output
    assert "Frieren" in result.output
    assert source.exists(), "dry-run must not touch files"


@respx.mock
def test_apply_renames_and_writes_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    source = tmp_path / "[SubsPlease] Frieren - 01 (1080p).mkv"
    source.touch()

    _mock_frieren()

    result = runner.invoke(app, [str(tmp_path), "--apply", "--yes"])

    assert result.exit_code == 0, result.output
    assert not source.exists(), "source file should have been renamed"

    expected = tmp_path / "Frieren: Beyond Journey's End - S01E01 - The Journey's End.mkv"
    # Colon is illegal on some filesystems; our sanitiser replaces it with a space.
    renamed = list(tmp_path.glob("Frieren*.mkv"))
    assert renamed, f"no renamed file found; got {list(tmp_path.iterdir())}"
    assert "S01E01" in renamed[0].name
    assert "The Journey" in renamed[0].name

    history = tmp_path / ".minifilebot" / "history"
    assert history.exists() and any(history.iterdir())
    _ = expected  # kept for documentation; not asserted directly


@respx.mock
def test_tmdb_id_override_bypasses_search(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    source = tmp_path / "totally_wrong_filename - 01.mkv"
    source.touch()

    # Search route should NEVER be called when --tmdb-id is provided.
    search_route = respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    respx.get(f"{TMDB_BASE_URL}/tv/209867").mock(
        return_value=httpx.Response(
            200, json={"id": 209867, "name": "Frieren: Beyond Journey's End"}
        )
    )
    respx.get(f"{TMDB_BASE_URL}/tv/209867/season/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "episodes": [
                    {"season_number": 1, "episode_number": 1, "name": "The Journey's End"},
                ]
            },
        )
    )

    result = runner.invoke(app, [str(tmp_path), "--tmdb-id", "209867"])

    assert result.exit_code == 0, result.output
    assert search_route.call_count == 0
    assert "Frieren" in result.output


def test_missing_api_key_exits_with_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    source = tmp_path / "x.mkv"
    source.touch()
    result = runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 2
    assert "TMDB_API_KEY" in result.output


@respx.mock
def test_missing_season_yields_helpful_detail(tmp_path: Path, monkeypatch) -> None:
    """Anime 'Nth Season' filenames frequently map to TMDB shows with only season 1."""
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    source = tmp_path / "Jujutsu Kaisen 2nd Season - 05.mkv"
    source.touch()

    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 95479,
                        "name": "JUJUTSU KAISEN",
                        "original_name": "\u547c\u5ef6",
                        "first_air_date": "2020-10-03",
                        "overview": "",
                    }
                ]
            },
        )
    )
    respx.get(f"{TMDB_BASE_URL}/tv/95479/season/2").mock(
        return_value=httpx.Response(404, json={"status_message": "Not found"})
    )
    respx.get(f"{TMDB_BASE_URL}/tv/95479").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 95479,
                "name": "JUJUTSU KAISEN",
                "seasons": [
                    {"season_number": 0, "name": "Specials"},
                    {"season_number": 1, "name": "Season 1"},
                ],
            },
        )
    )

    result = runner.invoke(app, [str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "no season" in result.output
    assert source.exists()


def test_empty_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(app, [str(empty)])
    assert result.exit_code == 0
    assert "No video files" in result.output
