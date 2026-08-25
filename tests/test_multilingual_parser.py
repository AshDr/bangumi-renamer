"""Regression tests for multilingual episode and season markers."""

from __future__ import annotations

from pathlib import Path

import pytest

from minifilebot.parser import ParseError, parse


@pytest.mark.parametrize(
    ("filename", "title", "season", "episode"),
    [
        ("凡人修仙传 第12集.mp4", "凡人修仙传", 1, 12),
        ("斗罗大陆 第03话.mkv", "斗罗大陆", 1, 3),
        ("葬送的芙莉蓮 第04話.mkv", "葬送的芙莉蓮", 1, 4),
        ("薬屋のひとりごと 第05話.mkv", "薬屋のひとりごと", 1, 5),
        ("Frieren EP 02.mkv", "Frieren", 1, 2),
        ("Frieren Ep. 03.mkv", "Frieren", 1, 3),
        (
            "The Apothecary Diaries Season 2 Episode 06.mkv",
            "The Apothecary Diaries",
            2,
            6,
        ),
        ("凡人修仙传 第2季 第03集.mkv", "凡人修仙传", 2, 3),
        (
            "Re：ゼロから始める異世界生活 第２期 第０１話.mkv",
            "Re：ゼロから始める異世界生活",
            2,
            1,
        ),
    ],
)
def test_parse_multilingual_markers(
    filename: str, title: str, season: int, episode: int
) -> None:
    result = parse(filename)

    assert result.title == title
    assert result.season == season
    assert result.episode == episode


def test_parse_reported_japanese_filename_with_release_metadata() -> None:
    filename = (
        "[DMG] Re：ゼロから始める休憩時間 第01話 "
        "[BDRip][HEVC_FLAC][1080P_Ma10P](C17E91BD).mkv"
    )

    result = parse(filename)

    assert result.title == "Re：ゼロから始める休憩時間"
    assert result.season == 1
    assert result.episode == 1
    assert result.release_group == "DMG"
    assert result.extension == "mkv"


@pytest.mark.parametrize(
    "filename",
    [
        "[SubsPlease] Frieren - 01 (1080p).mkv",
        "Attack.on.Titan.S04E01.1080p.mkv",
    ],
)
def test_existing_anitopy_formats_still_parse(filename: str) -> None:
    result = parse(filename)

    assert isinstance(result.source, Path)
    assert result.episode == 1


def test_multilingual_title_without_episode_is_rejected() -> None:
    with pytest.raises(ParseError):
        parse("葬送的芙莉蓮 [1080p].mkv")
