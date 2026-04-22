"""Shared pytest fixtures for GUI tests.

Force the off-screen Qt platform so pytest-qt works headless in CI and
without flashing windows during local runs.
"""

from __future__ import annotations

import os

# Must happen before QApplication is created by pytest-qt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

# QSettings is global per-user; isolate it per test so we don't clobber real
# user preferences when running locally.
from PySide6.QtCore import QCoreApplication, QSettings  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_qsettings(tmp_path, monkeypatch):
    QCoreApplication.setOrganizationName("MiniFileBotTest")
    QCoreApplication.setApplicationName("app")
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path / "qsettings"),
    )
    # Remove any stray env var that would otherwise leak a real key.
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    yield
