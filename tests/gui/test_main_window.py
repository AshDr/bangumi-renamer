"""Smoke tests for the PySide6 MainWindow.

These are intentionally narrow: construct the window, drive it through the
same paths a real user would, and assert the plan table ends up in the right
shape. TMDB is fully mocked via respx so the tests run offline.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import respx
from pytestqt.qtbot import QtBot

from minifilebot.gui import settings
from minifilebot.gui.main_window import MainWindow
from minifilebot.tmdb import TMDB_BASE_URL


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


def _build_window(qtbot: QtBot, tmp_path: Path) -> MainWindow:
    # Point the on-disk TMDB cache at a tmpdir so the worker doesn't pollute $XDG_CACHE.
    os.environ["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    settings.set_api_key("test-key")
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def _wait_scan_done(qtbot: QtBot, window: MainWindow) -> None:
    """Wait for the most recent ScanWorker to terminate AND its signals to drain."""
    qtbot.waitUntil(
        lambda: window._scan_worker is not None and window._scan_worker.isFinished(),
        timeout=5000,
    )
    # One more event-loop turn so queued _on_plan_ready() slot runs.
    qtbot.wait(50)


def test_empty_folder_shows_no_files_message(qtbot: QtBot, tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    window = _build_window(qtbot, tmp_path)

    window._load_folder(empty)
    _wait_scan_done(qtbot, window)

    assert window._model.rowCount() == 0
    assert "No video files" in window._drop_hint.text()


@respx.mock
def test_folder_with_sample_produces_ok_row(qtbot: QtBot, tmp_path: Path) -> None:
    folder = tmp_path / "videos"
    folder.mkdir()
    (folder / "[SubsPlease] Frieren - 01 (1080p).mkv").touch()
    _mock_frieren()

    window = _build_window(qtbot, tmp_path)
    window._load_folder(folder)
    _wait_scan_done(qtbot, window)

    assert window._model.rowCount() == 1
    item = window._model.item_at(0)
    assert item is not None
    assert item.status == "OK"
    assert item.target is not None
    assert "S01E01" in item.target.name
    # Apply action lights up once we have OK rows.
    assert window._apply_action.isEnabled()
