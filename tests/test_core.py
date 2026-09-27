"""Core pipeline tests for plan building and apply behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from bangumi_renamer.core import ManualNaming, apply_plan, build_plan
from bangumi_renamer.matcher import MatchResult
from bangumi_renamer.parser import ParsedFile
from bangumi_renamer.tmdb import Episode


class DummyClient:
    def __init__(self, episodes: list[Episode]) -> None:
        self._episodes = episodes
        self.season_calls: list[tuple[int, int]] = []

    def get_season(self, tv_id: int, season: int) -> list[Episode]:
        self.season_calls.append((tv_id, season))
        return self._episodes


def test_build_plan_reuses_match_and_season_cache(monkeypatch, tmp_path: Path) -> None:
    sources = [
        tmp_path / "[SubsPlease] Frieren - 01.mkv",
        tmp_path / "[SubsPlease] Frieren - 02.mkv",
    ]

    parsed_by_name = {
        sources[0].name: ParsedFile(
            source=sources[0],
            title="Frieren",
            season=1,
            episode=1,
            is_special=False,
            release_group="SubsPlease",
            extension="mkv",
        ),
        sources[1].name: ParsedFile(
            source=sources[1],
            title="Frieren",
            season=1,
            episode=2,
            is_special=False,
            release_group="SubsPlease",
            extension="mkv",
        ),
    }
    match_calls: list[str] = []

    def fake_parse(source: Path) -> ParsedFile:
        return parsed_by_name[source.name]

    def fake_match(title: str, *, client) -> MatchResult:
        _ = client
        match_calls.append(title)
        return MatchResult(tmdb_id=209867, name="Frieren", confidence=100.0, reason="test")

    monkeypatch.setattr("bangumi_renamer.core.parse", fake_parse)
    monkeypatch.setattr("bangumi_renamer.core.match", fake_match)

    client = DummyClient(
        [
            Episode(season=1, number=1, name="The Journey's End"),
            Episode(season=1, number=2, name="A Great Mage"),
        ]
    )

    plan = build_plan(sources, client=client, forced=None)

    assert [item.status for item in plan] == ["OK", "OK"]
    assert match_calls == ["Frieren"]
    assert client.season_calls == [(209867, 1)]
    assert plan[0].target is not None
    assert plan[0].target.name == "Frieren-S01E01.mkv"
    assert plan[1].target is not None
    assert plan[1].target.name == "Frieren-S01E02.mkv"


def test_build_plan_marks_duplicate_planned_target_as_conflict(
    monkeypatch, tmp_path: Path
) -> None:
    sources = [
        tmp_path / "show-01-source-a.mkv",
        tmp_path / "show-01-source-b.mkv",
    ]

    def fake_parse(source: Path) -> ParsedFile:
        return ParsedFile(
            source=source,
            title="Same Show",
            season=1,
            episode=1,
            is_special=False,
            release_group=None,
            extension="mkv",
        )

    monkeypatch.setattr("bangumi_renamer.core.parse", fake_parse)

    forced = MatchResult(tmdb_id=1, name="Same Show", confidence=100.0, reason="forced")
    client = DummyClient([Episode(season=1, number=1, name="Pilot")])

    plan = build_plan(sources, client=client, forced=forced)

    assert plan[0].status == "OK"
    assert plan[0].target is not None
    assert plan[0].target.name == "Same Show-S01E01.mkv"
    assert plan[1].status == "conflict"
    assert plan[1].target is not None
    assert plan[1].target.name == "Same Show-S01E01.mkv"
    assert plan[1].detail == "target exists: Same Show-S01E01.mkv"


def test_manual_plan_and_apply_without_metadata(tmp_path: Path) -> None:
    sources = [tmp_path / name for name in (
        "Unknown Show S03E01.mkv", "Unknown Show S03E01.zh-Hans.forced.srt", "02.mkv",
    )]
    for source in sources:
        source.write_text(source.name)
    plan = build_plan(sources, manual=ManualNaming(" Custom Show ", 2))
    assert all(source.exists() for source in sources)
    assert [item.target.name for item in plan] == [
        "Custom Show-S02E01.mkv", "Custom Show-S02E01.zh-hans.forced.srt",
        "Custom Show-S02E02.mkv",
    ]
    assert all(item.match is None and item.manual_title == "Custom Show" for item in plan)
    renames, history = apply_plan(plan, root=tmp_path)
    assert len(renames) == 3 and history.is_file()
    for source, target in renames:
        assert not source.exists()
        assert target.read_text() == source.name


def test_manual_plan_keeps_unparseable_files_and_handles_conflicts(tmp_path: Path) -> None:
    sources = [tmp_path / name for name in ("01.mkv", "unknown.mkv", "Show - 01-02.mkv")]
    for source in sources:
        source.touch()
    existing = tmp_path / "Custom-S00E01.mkv"
    existing.write_text("existing")
    plan = build_plan(sources, manual=ManualNaming("Custom", 0), on_conflict="skip")
    assert [item.status for item in plan] == ["conflict", "unparsed", "unparsed"]
    assert apply_plan(plan, root=tmp_path) == ([], None)
    assert all(source.exists() for source in sources)
    assert existing.read_text() == "existing"
    suffixed = build_plan(sources[:1], manual=ManualNaming("Custom", 0))
    assert suffixed[0].target.name == "Custom-S00E01 (1).mkv"


@pytest.mark.parametrize("title,season", [(" ", 1), ("Show", -1), ("Show", 1.5),
                                          ("Show", True), ("Show", 1000)])
def test_manual_naming_rejects_invalid_inputs(title, season) -> None:
    with pytest.raises(ValueError):
        ManualNaming(title, season)
