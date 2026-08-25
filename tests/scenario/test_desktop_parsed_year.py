from __future__ import annotations

from bangumi_renamer.core import PlanItem
from bangumi_renamer.desktop_bridge import _serialize_plan_item
from bangumi_renamer.parser import ParsedFile, parse


def _serialize_parsed_file(parsed: ParsedFile) -> dict[str, object]:
    item = PlanItem(
        source=parsed.source,
        parsed=parsed,
        match=None,
        target=None,
        status="OK",
    )
    return _serialize_plan_item(item)


def test_desktop_plan_serializes_filename_year() -> None:
    parsed = parse("[SubsPlease] Frieren (2023) - 01 (1080p).mkv")

    payload = _serialize_parsed_file(parsed)

    assert parsed.year == 2023
    assert payload["parsed"]["year"] == 2023  # type: ignore[index]


def test_desktop_plan_serializes_missing_year_as_null() -> None:
    parsed = parse("[SubsPlease] Frieren - 01 (1080p).mkv")

    payload = _serialize_parsed_file(parsed)

    assert parsed.year is None
    assert payload["parsed"]["year"] is None  # type: ignore[index]
