"""QAbstractTableModel that backs the main preview table.

Columns: #, Source, -> Target, Status. Row background colour hints at status
(green for OK, amber for recoverable issues, red for errors).
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from ..core import PlanItem

_COLUMNS = ("#", "Source", "-> Target", "Status")

_STATUS_COLORS: dict[str, QColor] = {
    "OK": QColor(46, 125, 50, 40),
    "unparsed": QColor(230, 145, 56, 60),
    "no match": QColor(230, 145, 56, 60),
    "no season": QColor(230, 145, 56, 60),
    "conflict": QColor(230, 145, 56, 60),
    "error": QColor(198, 40, 40, 60),
}


class PlanModel(QAbstractTableModel):
    def __init__(self, items: list[PlanItem] | None = None) -> None:
        super().__init__()
        self._items: list[PlanItem] = list(items or [])

    # ----- required Qt overrides ---------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: ARG002
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: ARG002
        return len(_COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return section + 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid():
            return None
        item = self._items[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return _cell_text(item, col)
        if role == Qt.ItemDataRole.BackgroundRole:
            color = _STATUS_COLORS.get(item.status)
            return QBrush(color) if color else None
        if role == Qt.ItemDataRole.ToolTipRole and item.detail:
            return item.detail
        return None

    # ----- helpers the view calls --------------------------------------------
    def items(self) -> list[PlanItem]:
        return list(self._items)

    def item_at(self, row: int) -> PlanItem | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def set_items(self, items: list[PlanItem]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def replace_item(self, row: int, item: PlanItem) -> None:
        if not 0 <= row < len(self._items):
            return
        self._items[row] = item
        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)

    def ok_count(self) -> int:
        return sum(1 for it in self._items if it.status == "OK" and it.target != it.source)


def _cell_text(item: PlanItem, col: int) -> str:
    if col == 0:
        return ""  # row number is provided by headerData()
    if col == 1:
        return item.source.name
    if col == 2:
        if item.target is not None and item.status == "OK":
            return item.target.name
        return item.detail or "-"
    if col == 3:
        return item.status
    return ""
