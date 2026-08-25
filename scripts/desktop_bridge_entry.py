"""PyInstaller entry point for the Tauri Python sidecar."""

from __future__ import annotations

from bangumi_renamer.desktop_bridge import main

if __name__ == "__main__":
    main()
