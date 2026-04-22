"""Dialog that lets the user pick a TMDB show when auto-match is wrong.

Equivalent to FileBot's "Select TV Show" dialog. The caller provides the list
of ``ScoredCandidate`` instances; this dialog returns the chosen one (or
``None`` if the user cancels).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..matcher import ScoredCandidate


class CandidateDialog(QDialog):
    def __init__(
        self,
        title: str,
        candidates: list[ScoredCandidate],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Pick match for '{title}'")
        self.setMinimumSize(620, 420)

        self._candidates = candidates
        self._selected: ScoredCandidate | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                f"TMDB candidates for <b>{title}</b> (sorted by confidence):",
                parent=self,
            )
        )

        self._list = QListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setAlternatingRowColors(True)
        for candidate in candidates:
            self._list.addItem(_make_item(candidate))
        if candidates:
            self._list.setCurrentRow(0)
        self._list.itemDoubleClicked.connect(lambda _item: self._accept_current())
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_current(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._candidates):
            self._selected = self._candidates[row]
            self.accept()

    def selected(self) -> ScoredCandidate | None:
        return self._selected


def _make_item(candidate: ScoredCandidate) -> QListWidgetItem:
    year = f"({candidate.first_air_year})" if candidate.first_air_year else ""
    title = f"{candidate.name} {year}".strip()
    # Show original name on its own line when it differs — the user often
    # recognises the show by its native title.
    subtitle_bits: list[str] = []
    if candidate.original_name and candidate.original_name != candidate.name:
        subtitle_bits.append(candidate.original_name)
    subtitle_bits.append(candidate.reason)
    if candidate.overview:
        subtitle_bits.append(candidate.overview.splitlines()[0][:140])
    text = f"{title}\n    {'  —  '.join(subtitle_bits)}"
    item = QListWidgetItem(text)
    item.setData(Qt.ItemDataRole.UserRole, candidate.tmdb_id)
    return item
