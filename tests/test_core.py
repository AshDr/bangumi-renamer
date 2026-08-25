"""Core pipeline tests for plan building and apply behavior."""

from __future__ import annotations

from pathlib import Path

from bangumi_renamer.core import build_plan
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
    assert plan[0].target.name == "Frieren - S01E01 - The Journey's End.mkv"
    assert plan[1].target is not None
    assert plan[1].target.name == "Frieren - S01E02 - A Great Mage.mkv"


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
    assert plan[0].target.name == "Same Show - S01E01 - Pilot.mkv"
    assert plan[1].status == "conflict"
    assert plan[1].target is not None
    assert plan[1].target.name == "Same Show - S01E01 - Pilot.mkv"
    assert plan[1].detail == "target exists: Same Show - S01E01 - Pilot.mkv"
