"""Scenarios for the compact series and episode filename template."""

from bangumi_renamer.renamer import build_new_name


def test_compact_filename_omits_episode_title_and_separator_spaces() -> None:
    result = build_new_name(
        series="Frieren",
        season=1,
        episode=3,
        episode_title="The Journey's End",
        extension="mkv",
    )

    assert result == "Frieren-S01E03.mkv"


def test_compact_filename_removes_trailing_series_hyphen() -> None:
    result = build_new_name(
        series="Re:ZERO -Starting Life in Another World-",
        season=1,
        episode=3,
        episode_title="Starting Life from Zero in Another World",
        extension="mkv",
    )

    assert result == "Re ZERO -Starting Life in Another World-S01E03.mkv"
