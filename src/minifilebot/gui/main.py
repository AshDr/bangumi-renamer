"""Entry point: ``minifilebot-gui`` script hits ``run()``."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication


def run() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    # Lazy import to keep this module cheap when invoked for --help etc.
    from .main_window import MainWindow

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
