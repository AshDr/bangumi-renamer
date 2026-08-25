"""Parser tests driven by fixtures/filenames.txt so new samples drop in easily."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from bangumi_renamer.parser import ParsedFile, ParseError, parse

FIXTURE = Path(__file__).parent / "fixtures" / "filenames.txt"


@dataclass
class Case:
    filename: str
    expected_title: str | None
    expected_season: int | None
    expected_episode: int | None

    @property
    def should_parse(self) -> bool:
        return self.expected_title is not None


def _load_cases() -> list[Case]:
    cases: list[Case] = []
    for raw in FIXTURE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        assert len(parts) == 4, f"bad fixture line: {raw!r}"
        filename, title, season, episode = parts
        cases.append(
            Case(
                filename=filename,
                expected_title=title or None,
                expected_season=int(season) if season else None,
                expected_episode=int(episode) if episode else None,
            )
        )
    return cases


CASES = _load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c.filename for c in CASES])
def test_parse_matches_fixture(case: Case) -> None:
    if not case.should_parse:
        with pytest.raises(ParseError):
            parse(case.filename)
        return

    result = parse(case.filename)
    assert isinstance(result, ParsedFile)
    assert result.title == case.expected_title
    assert result.season == case.expected_season
    assert result.episode == case.expected_episode


def test_parse_success_rate_meets_acceptance() -> None:
    """PRD §8 requires >= 70% parse rate on realistic filenames."""
    parseable = [c for c in CASES if c.should_parse]
    successes = 0
    for case in parseable:
        try:
            parse(case.filename)
            successes += 1
        except ParseError:
            pass
    rate = successes / len(parseable)
    assert rate >= 0.70, f"parse success rate {rate:.0%} < 70% target"


def test_parse_captures_release_group() -> None:
    result = parse("[SubsPlease] Frieren - 01 (1080p).mkv")
    assert result.release_group == "SubsPlease"


def test_parse_defaults_missing_season_to_one() -> None:
    result = parse("Chainsaw Man - 04.mkv")
    assert result.season == 1


def test_parse_preserves_source_path() -> None:
    src = "/tmp/anime/[SubsPlease] Frieren - 01 (1080p).mkv"
    result = parse(src)
    assert str(result.source) == src
