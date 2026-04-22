"""Top-level window: menu, toolbar, drag-drop area, preview table, status bar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core import PlanItem
from ..matcher import ScoredCandidate
from . import settings
from .candidate_dialog import CandidateDialog
from .plan_model import PlanModel
from .plan_view import PlanView
from .settings_dialog import SettingsDialog
from .worker import ApplyWorker, CandidateFetchWorker, RebuildWorker, ScanWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MiniFileBot")
        self.resize(960, 560)
        self.setAcceptDrops(True)

        self._model = PlanModel()
        self._current_root: Path | None = None
        self._scan_worker: ScanWorker | None = None
        self._apply_worker: ApplyWorker | None = None
        self._candidate_worker: CandidateFetchWorker | None = None
        self._rebuild_worker: RebuildWorker | None = None
        self._pending_pick_row: int | None = None

        self._view = PlanView(self)
        self._view.setModel(self._model)
        self._view.pick_match_requested.connect(self._start_pick_match)

        self._drop_hint = QLabel(
            "Drop a folder here, or use File -> Open Folder...",
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self._drop_hint.setStyleSheet("color: #888; padding: 24px;")

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._drop_hint)
        layout.addWidget(self._view)
        self._view.setVisible(False)
        self.setCentralWidget(central)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(200)
        self._status_label = QLabel("Ready", self)
        self.statusBar().addWidget(self._status_label, 1)
        self.statusBar().addPermanentWidget(self._progress)

        self._build_menu_and_toolbar()
        self._refresh_action_enabled()

        # First run with no API key: prompt immediately so the user isn't stuck
        # wondering why "Open Folder" does nothing.
        if not settings.get_api_key():
            self._open_settings()

    # ----- menu / toolbar -----------------------------------------------------
    def _build_menu_and_toolbar(self) -> None:
        self._open_action = QAction("Open Folder...", self)
        self._open_action.setShortcut("Ctrl+O")
        self._open_action.triggered.connect(self._choose_folder)

        self._rescan_action = QAction("Rescan", self)
        self._rescan_action.setShortcut("Ctrl+R")
        self._rescan_action.triggered.connect(self._rescan)

        self._apply_action = QAction("Apply", self)
        self._apply_action.setShortcut("Ctrl+Return")
        self._apply_action.triggered.connect(self._apply)

        self._settings_action = QAction("Settings...", self)
        self._settings_action.setShortcut("Ctrl+,")
        self._settings_action.triggered.connect(self._open_settings)

        self._quit_action = QAction("Quit", self)
        self._quit_action.setShortcut("Ctrl+Q")
        self._quit_action.triggered.connect(self.close)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._rescan_action)
        file_menu.addSeparator()
        file_menu.addAction(self._apply_action)
        file_menu.addSeparator()
        file_menu.addAction(self._settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self._quit_action)

        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        toolbar.addAction(self._open_action)
        toolbar.addAction(self._rescan_action)
        toolbar.addAction(self._apply_action)
        toolbar.addSeparator()
        toolbar.addAction(self._settings_action)
        self.addToolBar(toolbar)

    def _refresh_action_enabled(self) -> None:
        has_api_key = bool(settings.get_api_key())
        busy = any(
            w is not None and w.isRunning()
            for w in (
                self._scan_worker,
                self._apply_worker,
                self._candidate_worker,
                self._rebuild_worker,
            )
        )

        self._open_action.setEnabled(has_api_key and not busy)
        self._rescan_action.setEnabled(
            has_api_key and not busy and self._current_root is not None
        )
        self._apply_action.setEnabled(not busy and self._model.ok_count() > 0)

    # ----- folder loading -----------------------------------------------------
    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Open Folder", str(Path.home())
        )
        if folder:
            self._load_folder(Path(folder))

    def _rescan(self) -> None:
        if self._current_root is not None:
            self._load_folder(self._current_root)

    def _load_folder(self, root: Path) -> None:
        api_key = settings.get_api_key()
        if not api_key:
            QMessageBox.information(
                self, "Set API key", "A TMDB API key is required before scanning."
            )
            self._open_settings()
            return

        self._current_root = root
        self._set_busy(True, f"Scanning {root}...")
        self._scan_worker = ScanWorker(
            root,
            api_key=api_key,
            lang=settings.get_lang(),
            on_conflict=settings.get_on_conflict(),
            parent=self,
        )
        self._scan_worker.progress.connect(self._on_progress)
        self._scan_worker.finished_plan.connect(self._on_plan_ready)
        self._scan_worker.failed.connect(self._on_failed)
        self._scan_worker.finished.connect(self._on_worker_done)
        self._scan_worker.start()

    def _on_plan_ready(self, items: list[PlanItem]) -> None:
        self._model.set_items(items)
        if not items:
            self._drop_hint.setText("No video files found in this folder.")
            self._drop_hint.setVisible(True)
            self._view.setVisible(False)
            self._status_label.setText(f"Done. 0 files in {self._current_root}")
            return
        self._drop_hint.setVisible(False)
        self._view.setVisible(True)
        self._view.resizeColumnsToContents()
        self._status_label.setText(self._summary_text())

    def _summary_text(self) -> str:
        counts: dict[str, int] = {}
        for item in self._model.items():
            counts[item.status] = counts.get(item.status, 0) + 1
        parts = [f"{s}: {n}" for s, n in sorted(counts.items())]
        total = sum(counts.values())
        return f"{total} files  |  " + "  ".join(parts) if parts else f"{total} files"

    # ----- apply --------------------------------------------------------------
    def _apply(self) -> None:
        if self._current_root is None:
            return
        to_apply = [
            item
            for item in self._model.items()
            if item.status == "OK" and item.target is not None and item.target != item.source
        ]
        if not to_apply:
            return
        confirm = QMessageBox.question(
            self,
            "Apply renames?",
            f"Rename {len(to_apply)} file(s) now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True, "Applying renames...")
        self._apply_worker = ApplyWorker(to_apply, root=self._current_root, parent=self)
        self._apply_worker.progress.connect(self._on_progress)
        self._apply_worker.finished_apply.connect(self._on_apply_done)
        self._apply_worker.failed.connect(self._on_failed)
        self._apply_worker.finished.connect(self._on_worker_done)
        self._apply_worker.start()

    def _on_apply_done(self, count: int, history_path: object) -> None:
        if count == 0:
            self._status_label.setText("No files needed renaming.")
        else:
            self._status_label.setText(
                f"Renamed {count} file(s). History: {history_path}"
            )
        # Refresh the plan so the table reflects the new filenames.
        if self._current_root is not None:
            self._load_folder(self._current_root)

    # ----- manual candidate pick ---------------------------------------------
    def _start_pick_match(self, row: int) -> None:
        item = self._model.item_at(row)
        if item is None or item.parsed is None:
            QMessageBox.information(
                self,
                "Nothing to match",
                "This row has no parsed title (filename could not be parsed).",
            )
            return
        api_key = settings.get_api_key()
        if not api_key:
            self._open_settings()
            return

        self._pending_pick_row = row
        self._set_busy(True, f"Searching TMDB for '{item.parsed.title}'...")
        self._candidate_worker = CandidateFetchWorker(
            item.parsed.title,
            api_key=api_key,
            lang=settings.get_lang(),
            parent=self,
        )
        self._candidate_worker.finished_candidates.connect(self._on_candidates_ready)
        self._candidate_worker.failed.connect(self._on_failed)
        self._candidate_worker.finished.connect(self._on_worker_done)
        self._candidate_worker.start()

    def _on_candidates_ready(self, query: str, candidates: list[ScoredCandidate]) -> None:
        row = self._pending_pick_row
        self._pending_pick_row = None
        if row is None:
            return
        if not candidates:
            QMessageBox.information(
                self, "No candidates", f"TMDB returned no results for '{query}'."
            )
            return
        dialog = CandidateDialog(query, candidates, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        chosen = dialog.selected()
        if chosen is None:
            return
        self._rebuild_with_forced_id(query, chosen.tmdb_id)

    def _rebuild_with_forced_id(self, title: str, tmdb_id: int) -> None:
        """Re-run the plan for every row whose parsed title matches ``title``."""
        if self._current_root is None:
            return
        affected_sources: list[Path] = [
            item.source
            for item in self._model.items()
            if item.parsed is not None and item.parsed.title == title
        ]
        if not affected_sources:
            return
        api_key = settings.get_api_key()
        if not api_key:
            return

        self._set_busy(True, f"Rebuilding {len(affected_sources)} row(s) with tmdb_id={tmdb_id}...")
        self._rebuild_worker = RebuildWorker(
            affected_sources,
            tmdb_id=tmdb_id,
            api_key=api_key,
            lang=settings.get_lang(),
            on_conflict=settings.get_on_conflict(),
            parent=self,
        )
        self._rebuild_worker.finished_rebuild.connect(self._on_rebuild_done)
        self._rebuild_worker.failed.connect(self._on_failed)
        self._rebuild_worker.finished.connect(self._on_worker_done)
        self._rebuild_worker.start()

    def _on_rebuild_done(self, new_items: list[PlanItem]) -> None:
        # Splice the rebuilt items back into the existing model by source path.
        by_source = {item.source: item for item in new_items}
        for row, existing in enumerate(self._model.items()):
            replacement = by_source.get(existing.source)
            if replacement is not None:
                self._model.replace_item(row, replacement)
        self._view.resizeColumnsToContents()
        self._status_label.setText(self._summary_text())
        self._refresh_action_enabled()

    # ----- misc UI glue -------------------------------------------------------
    def _on_progress(self, idx: int, total: int, name: str) -> None:
        self._progress.setVisible(True)
        self._progress.setMaximum(total)
        self._progress.setValue(idx)
        self._status_label.setText(f"[{idx}/{total}] {name}")

    def _on_failed(self, message: str) -> None:
        self._set_busy(False, "")
        QMessageBox.critical(self, "Error", message)
        self._status_label.setText("Error. See dialog for details.")

    def _on_worker_done(self) -> None:
        self._set_busy(False, "")

    def _set_busy(self, busy: bool, message: str) -> None:
        self._progress.setVisible(busy)
        if busy:
            self._status_label.setText(message)
            self._progress.setValue(0)
        self._refresh_action_enabled()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()
        self._refresh_action_enabled()

    # ----- drag-drop ----------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        for url in urls:
            path = Path(url.toLocalFile())
            if path.is_dir():
                self._load_folder(path)
                return
        QMessageBox.information(
            self, "Not a folder", "Drop a single folder containing video files."
        )

    def closeEvent(self, event: object) -> None:
        # Give any live workers a moment to stop before the window is destroyed.
        workers = (
            self._scan_worker,
            self._apply_worker,
            self._candidate_worker,
            self._rebuild_worker,
        )
        for worker in workers:
            if worker is not None and worker.isRunning():
                worker.requestInterruption()
                worker.wait(3000)
        super().closeEvent(event)  # type: ignore[arg-type]
