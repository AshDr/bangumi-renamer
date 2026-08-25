"""Build the Python core as the sidecar bundled by Tauri.

Run with: uv run --extra desktop python scripts/build_desktop_bridge.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "scripts" / "desktop_bridge_entry.py"
BIN_DIR = ROOT / "desktop" / "src-tauri" / "bin"
WORK_DIR = ROOT / "build" / "desktop-bridge"
CACHE_DIR = ROOT / ".pyinstaller-cache"


def main() -> None:
    """Build a deterministic one-file sidecar into the Tauri resource directory."""
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller is None:
        raise SystemExit(
            "PyInstaller is not installed. Run with `uv run --extra desktop python "
            "scripts/build_desktop_bridge.py`."
        )

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    build_environment = os.environ.copy()
    build_environment["PYINSTALLER_CONFIG_DIR"] = str(CACHE_DIR)
    subprocess.run(
        [
            pyinstaller,
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "minifilebot-bridge",
            "--distpath",
            str(BIN_DIR),
            "--workpath",
            str(WORK_DIR / "work"),
            "--specpath",
            str(WORK_DIR),
            str(ENTRY),
        ],
        cwd=ROOT,
        env=build_environment,
        check=True,
    )


if __name__ == "__main__":
    main()
