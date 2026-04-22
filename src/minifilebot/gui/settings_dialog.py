"""Modal dialog for TMDB key / language / conflict policy."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from . import settings


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)

        self._key_edit = QLineEdit(self)
        # Mask the API key so it doesn't leak in screenshots or screenshares.
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setText(settings.get_api_key())
        self._key_edit.setPlaceholderText("TMDB v3 API key")

        self._lang_edit = QLineEdit(self)
        self._lang_edit.setText(settings.get_lang())
        self._lang_edit.setPlaceholderText("e.g. en-US, ja-JP, zh-CN")

        self._conflict = QComboBox(self)
        self._conflict.addItems(["suffix", "skip", "overwrite"])
        self._conflict.setCurrentText(settings.get_on_conflict())

        form = QFormLayout()
        form.addRow("TMDB API Key:", self._key_edit)
        form.addRow("Language:", self._lang_edit)
        form.addRow("On conflict:", self._conflict)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _save_and_accept(self) -> None:
        settings.set_api_key(self._key_edit.text())
        settings.set_lang(self._lang_edit.text().strip() or "en-US")
        settings.set_on_conflict(self._conflict.currentText())
        self.accept()
