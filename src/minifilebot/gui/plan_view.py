"""QTableView subclass with a context menu for manual match override.

The "Pick different match…" action is wired in Step 5 by ``MainWindow``; this
view just surfaces the right-click menu and delegates via a Qt signal.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView, QMenu, QTableView, QWidget


class PlanView(QTableView):
    pick_match_requested = Signal(int)  # row index

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
        self.setSelectionMode(self.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(False)
        self.setContextMenuPolicy(
            self.contextMenuPolicy().__class__.CustomContextMenu
        )
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos: QPoint) -> None:
        index = self.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        menu = QMenu(self)
        action = QAction("Pick different match...", menu)
        action.triggered.connect(lambda _checked=False, r=row: self.pick_match_requested.emit(r))
        menu.addAction(action)
        menu.exec(self.viewport().mapToGlobal(pos))
