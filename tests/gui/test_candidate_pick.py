"""Tests for the manual candidate picker flow.

Simulates: scan a JJK folder that TMDB can't resolve to season 2, then right-
click the failing row and pick an alternate TMDB id. The row's target name
should reflect the chosen show.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import respx
from PySide6.QtWidgets import QDialog
from pytestqt.qtbot import QtBot

from minifilebot.gui import settings
from minifilebot.gui.candidate_dialog import CandidateDialog
from minifilebot.gui.main_window import MainWindow
from minifilebot.tmdb import TMDB_BASE_URL


def _install_tmdb_mocks() -> None:
    # /search/tv returns two candidates for "Jujutsu Kaisen 2nd Season".
    # respx's default match ignores extra query params, so we don't constrain
    # on language/api_key/include_adult.
    respx.get(f"{TMDB_BASE_URL}/search/tv").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 95479,
                        "name": "JUJUTSU KAISEN",
                        "original_name": "Juujutsu Kaisen",
                        "first_air_date": "2020-10-03",
                        "overview": "",
                    },
                    {
                        "id": 222222,
                        "name": "Jujutsu Kaisen Season 2",
                        "original_name": "Juujutsu Kaisen 2nd",
                        "first_air_date": "2023-07-06",
                        "overview": "Sequel season.",
                    },
                ]
            },
        )
    )
    # Auto-match picks 95479 (first by confidence); season 2 404s.
    respx.get(f"{TMDB_BASE_URL}/tv/95479/season/2").mock(
        return_value=httpx.Response(404, json={"status_message": "Not found"})
    )
    respx.get(f"{TMDB_BASE_URL}/tv/95479").mock(
        return_value=httpx.Response(
            200,
            json={"id": 95479, "name": "JUJUTSU KAISEN", "seasons": [{"season_number": 1}]},
        )
    )
    # Forcing 222222 returns a valid season 2.
    respx.get(f"{TMDB_BASE_URL}/tv/222222").mock(
        return_value=httpx.Response(
            200, json={"id": 222222, "name": "Jujutsu Kaisen Season 2"}
        )
    )
    respx.get(f"{TMDB_BASE_URL}/tv/222222/season/2").mock(
        return_value=httpx.Response(
            200,
            json={
                "episodes": [
                    {"season_number": 2, "episode_number": 5, "name": "The Right Hand"},
                ]
            },
        )
    )


@respx.mock
def test_pick_match_updates_row_with_forced_id(
    qtbot: QtBot, tmp_path: Path, monkeypatch
) -> None:
    os.environ["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    settings.set_api_key("test-key")

    folder = tmp_path / "videos"
    folder.mkdir()
    (folder / "Jujutsu Kaisen 2nd Season - 05.mkv").touch()
    _install_tmdb_mocks()

    window = MainWindow()
    qtbot.addWidget(window)

    window._load_folder(folder)
    qtbot.waitUntil(lambda: window._model.rowCount() == 1, timeout=5000)
    assert window._model.item_at(0).status == "no season"

    # Monkeypatch CandidateDialog.exec to auto-select the 222222 entry.
    def fake_exec(self):
        for row in range(self._list.count()):
            if self._candidates[row].tmdb_id == 222222:
                self._list.setCurrentRow(row)
                self._selected = self._candidates[row]
                return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(CandidateDialog, "exec", fake_exec)

    window._start_pick_match(0)
    # Wait for the full chain: candidate fetch -> dialog -> rebuild -> model update.
    qtbot.waitUntil(
        lambda: (
            window._model.item_at(0) is not None
            and window._model.item_at(0).match is not None
            and window._model.item_at(0).match.tmdb_id == 222222
        ),
        timeout=10000,
    )

    row0 = window._model.item_at(0)
    assert row0.status == "OK"
    assert row0.target is not None
    assert "Jujutsu Kaisen Season 2" in row0.target.name
    assert "S02E05" in row0.target.name
