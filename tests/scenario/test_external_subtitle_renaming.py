"""Acceptance tests for external subtitle discovery and renaming."""

from __future__ import annotations

from pathlib import Path

from bangumi_renamer.core import apply_plan, build_plan
from bangumi_renamer.matcher import MatchResult
from bangumi_renamer.scanner import scan
from bangumi_renamer.tmdb import Episode


class SubtitleClient:
    """Return deterministic episode metadata without contacting TMDB."""

    def get_season(self, tv_id: int, season: int) -> list[Episode]:
        assert (tv_id, season) == (1, 1)
        return [Episode(season=1, number=1, name="Episode One")]


def _forced_match() -> MatchResult:
    return MatchResult(tmdb_id=1, name="Re Zero", confidence=100.0, reason="test")


def test_scan_discovers_common_external_subtitles(tmp_path: Path) -> None:
    names = {
        "Show - 01.mkv",
        "Show - 01.chs.ass",
        "Show - 01.cht.srt",
        "Show - 01.sup",
    }
    for name in names:
        (tmp_path / name).touch()
    (tmp_path / "notes.txt").touch()

    assert {path.name for path in scan(tmp_path)} == names


def test_scan_skips_subtitles_in_hidden_directories(tmp_path: Path) -> None:
    hidden = tmp_path / ".bangumi-renamer"
    hidden.mkdir()
    (hidden / "Show - 01.chs.ass").touch()
    visible = tmp_path / "Show - 01.mkv"
    visible.touch()

    assert scan(tmp_path) == [visible]


def test_plan_preserves_language_and_format_suffixes(tmp_path: Path) -> None:
    sources = [
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].chs.ass",
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].cht.ass",
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].zh-Hans.forced.srt",
    ]

    plan = build_plan(sources, client=SubtitleClient(), forced=_forced_match())

    assert [item.status for item in plan] == ["OK", "OK", "OK"]
    assert [item.target.name for item in plan if item.target is not None] == [
        "Re Zero-S01E01.chs.ass",
        "Re Zero-S01E01.cht.ass",
        "Re Zero-S01E01.zh-hans.forced.srt",
    ]


def test_apply_renames_video_and_external_subtitles_together(tmp_path: Path) -> None:
    sources = [
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].mkv",
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].chs.ass",
        tmp_path / "[DMG] Reゼロから始める異世界生活 [01].cht.ass",
    ]
    for source in sources:
        source.touch()

    plan = build_plan(scan(tmp_path), client=SubtitleClient(), forced=_forced_match())
    renames, history_path = apply_plan(plan, root=tmp_path)

    assert len(renames) == 3
    assert history_path is not None and history_path.exists()
    assert {target.name for _, target in renames} == {
        "Re Zero-S01E01.mkv",
        "Re Zero-S01E01.chs.ass",
        "Re Zero-S01E01.cht.ass",
    }
    assert all(not source.exists() for source in sources)


def test_conflict_suffix_stays_before_compound_subtitle_extension(tmp_path: Path) -> None:
    source = tmp_path / "[DMG] Reゼロから始める異世界生活 [01].chs.ass"
    existing = tmp_path / "Re Zero-S01E01.chs.ass"
    source.touch()
    existing.touch()

    plan = build_plan([source], client=SubtitleClient(), forced=_forced_match())

    assert plan[0].target == tmp_path / "Re Zero-S01E01 (1).chs.ass"
