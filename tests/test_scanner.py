"""Scanner tests."""

from __future__ import annotations

from pathlib import Path

from minifilebot.scanner import scan


def test_scan_directory_finds_videos(tmp_path: Path) -> None:
    (tmp_path / "a.mkv").touch()
    (tmp_path / "b.mp4").touch()
    (tmp_path / "c.txt").touch()
    result = scan(tmp_path)
    assert [p.name for p in result] == ["a.mkv", "b.mp4"]


def test_scan_recurses(tmp_path: Path) -> None:
    nested = tmp_path / "Season 1"
    nested.mkdir()
    (nested / "ep.mkv").touch()
    result = scan(tmp_path)
    assert len(result) == 1
    assert result[0].name == "ep.mkv"


def test_scan_skips_hidden_dirs(tmp_path: Path) -> None:
    hidden = tmp_path / ".minifilebot"
    hidden.mkdir()
    (hidden / "history.mkv").touch()
    (tmp_path / "real.mkv").touch()
    result = scan(tmp_path)
    assert [p.name for p in result] == ["real.mkv"]


def test_scan_single_file_returns_it(tmp_path: Path) -> None:
    target = tmp_path / "movie.mkv"
    target.touch()
    assert scan(target) == [target]


def test_scan_single_non_video_file(tmp_path: Path) -> None:
    target = tmp_path / "notes.txt"
    target.touch()
    assert scan(target) == []
