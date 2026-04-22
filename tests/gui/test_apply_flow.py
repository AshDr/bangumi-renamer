"""Tests for the GUI's apply flow: confirm dialog -> worker -> files renamed."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import respx
from PySide6.QtWidgets import QMessageBox
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
                        "name": "Frieren",
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
                    {"season_number": 1, "episode_number": 1, "name": "Journey's End"},
                ]
            },
        )
    )


def _wait_worker(qtbot: QtBot, worker_attr) -> None:
    qtbot.waitUntil(
        lambda: worker_attr() is not None and worker_attr().isFinished(), timeout=5000
    )
    qtbot.wait(80)


@respx.mock
def test_apply_renames_file_and_writes_history(
    qtbot: QtBot, tmp_path: Path, monkeypatch
) -> None:
    os.environ["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    settings.set_api_key("test-key")

    folder = tmp_path / "videos"
    folder.mkdir()
    source = folder / "[SubsPlease] Frieren - 01 (1080p).mkv"
    source.touch()
    _mock_frieren()

    # Auto-confirm the "Rename N file(s)?" dialog so the test is non-interactive.
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)

    window = MainWindow()
    qtbot.addWidget(window)

    window._load_folder(folder)
    _wait_worker(qtbot, lambda: window._scan_worker)
    assert window._model.rowCount() == 1
    assert window._apply_action.isEnabled()

    window._apply()
    _wait_worker(qtbot, lambda: window._apply_worker)
    # After apply, the window rescans — wait for the follow-up scan too.
    _wait_worker(qtbot, lambda: window._scan_worker)

    # Original file gone, renamed file present, history journal written.
    assert not source.exists()
    renamed = list(folder.glob("Frieren*.mkv"))
    assert renamed, f"no renamed file found; got {list(folder.iterdir())}"
    assert "S01E01" in renamed[0].name
    history_dir = folder / ".minifilebot" / "history"
    assert history_dir.exists() and any(history_dir.iterdir())
