"""Renamer tests: template, sanitisation, conflict handling."""

from __future__ import annotations

from pathlib import Path

from bangumi_renamer.renamer import build_new_name, resolve_conflict, sanitize_component


def test_build_new_name_basic() -> None:
    assert (
        build_new_name(
            series="Frieren",
            season=1,
            episode=1,
            episode_title="The Journey's End",
            extension="mkv",
        )
        == "Frieren - S01E01 - The Journey's End.mkv"
    )


def test_build_new_name_without_episode_title() -> None:
    assert (
        build_new_name(series="Bocchi", season=1, episode=3, episode_title="", extension="mp4")
        == "Bocchi - S01E03.mp4"
    )


def test_build_new_name_zero_pads_double_digits() -> None:
    result = build_new_name(
        series="Bleach", season=12, episode=140, episode_title="Title", extension="mkv"
    )
    assert "S12E140" in result


def test_sanitize_component_strips_illegal_windows_chars() -> None:
    assert sanitize_component('a<b>c:d"e/f\\g|h?i*j') == "a b c d e f g h i j"


def test_sanitize_component_trims_trailing_dot_and_space() -> None:
    assert sanitize_component("Trailing... ") == "Trailing"


def test_sanitize_component_never_returns_empty() -> None:
    assert sanitize_component("///") == "_"


def test_resolve_conflict_no_collision(tmp_path: Path) -> None:
    target = tmp_path / "new.mkv"
    assert resolve_conflict(target) == target


def test_resolve_conflict_suffix(tmp_path: Path) -> None:
    target = tmp_path / "new.mkv"
    target.touch()
    result = resolve_conflict(target)
    assert result == tmp_path / "new (1).mkv"


def test_resolve_conflict_skip(tmp_path: Path) -> None:
    target = tmp_path / "new.mkv"
    target.touch()
    assert resolve_conflict(target, on_conflict="skip") is None


def test_resolve_conflict_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "new.mkv"
    target.touch()
    assert resolve_conflict(target, on_conflict="overwrite") == target
