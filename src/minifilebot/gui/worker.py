"""Background ``QThread`` wrappers for scan + build_plan and for apply_plan.

Keeping all TMDB I/O off the GUI thread is mandatory — httpx calls can block
for seconds and Qt will beachball if we run them on the main thread.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ..core import PlanItem, apply_plan, build_plan
from ..matcher import MatchResult, ScoredCandidate, force_match, search_candidates
from ..scanner import scan
from ..tmdb import TmdbClient, TmdbError


class ScanWorker(QThread):
    """Scan a directory, parse filenames, resolve TMDB, emit the plan."""

    progress = Signal(int, int, str)  # current, total, source filename
    finished_plan = Signal(list)       # list[PlanItem]
    failed = Signal(str)

    def __init__(
        self,
        root: Path,
        *,
        api_key: str,
        lang: str,
        on_conflict: str,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = root
        self._api_key = api_key
        self._lang = lang
        self._on_conflict = on_conflict

    def run(self) -> None:
        try:
            files = scan(self._root)
            if not files:
                # Emit an empty plan so the view can show "no files" without error.
                self.finished_plan.emit([])
                return
            client = TmdbClient(api_key=self._api_key, lang=self._lang)
            try:
                plan = build_plan(
                    files=files,
                    client=client,
                    forced=None,
                    on_conflict=self._on_conflict,
                    progress_cb=self._emit_progress,
                )
            finally:
                client.close()
            self.finished_plan.emit(plan)
        except TmdbError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surface any crash to the UI
            self.failed.emit(f"scan failed: {exc}")

    def _emit_progress(self, idx: int, total: int, source: Path) -> None:
        self.progress.emit(idx, total, source.name)


class CandidateFetchWorker(QThread):
    """Fetch TMDB candidates for a given title (for the picker dialog)."""

    finished_candidates = Signal(str, list)  # query_title, list[ScoredCandidate]
    failed = Signal(str)

    def __init__(
        self,
        query: str,
        *,
        api_key: str,
        lang: str,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._query = query
        self._api_key = api_key
        self._lang = lang

    def run(self) -> None:
        try:
            client = TmdbClient(api_key=self._api_key, lang=self._lang)
            try:
                candidates: list[ScoredCandidate] = search_candidates(
                    self._query, client=client
                )
            finally:
                client.close()
            self.finished_candidates.emit(self._query, candidates)
        except TmdbError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"candidate search failed: {exc}")


class RebuildWorker(QThread):
    """Re-compute plan entries for a subset of files, forcing a specific TMDB id."""

    finished_rebuild = Signal(list)  # list[PlanItem]
    failed = Signal(str)

    def __init__(
        self,
        files: list[Path],
        *,
        tmdb_id: int,
        api_key: str,
        lang: str,
        on_conflict: str,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._files = files
        self._tmdb_id = tmdb_id
        self._api_key = api_key
        self._lang = lang
        self._on_conflict = on_conflict

    def run(self) -> None:
        try:
            client = TmdbClient(api_key=self._api_key, lang=self._lang)
            try:
                forced: MatchResult = force_match(self._tmdb_id, client=client)
                plan = build_plan(
                    files=self._files,
                    client=client,
                    forced=forced,
                    on_conflict=self._on_conflict,
                )
            finally:
                client.close()
            self.finished_rebuild.emit(plan)
        except TmdbError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"rebuild failed: {exc}")


class ApplyWorker(QThread):
    """Execute a prepared plan on disk."""

    progress = Signal(int, int, str)
    finished_apply = Signal(int, object)  # count, history_path or None
    failed = Signal(str)

    def __init__(
        self,
        items: list[PlanItem],
        *,
        root: Path,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._items = items
        self._root = root

    def run(self) -> None:
        try:
            renames, history_path = apply_plan(
                self._items, root=self._root, progress_cb=self._emit_progress
            )
            self.finished_apply.emit(len(renames), history_path)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"apply failed: {exc}")

    def _emit_progress(self, idx: int, total: int, source: Path) -> None:
        self.progress.emit(idx, total, source.name)
