from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_NAME = "".join(("mini", "file", "bot"))
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".npm-cache",
    ".pytest_cache",
    ".pyinstaller-cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "build",
    "completed-tdd-archives",
    "dist",
    "node_modules",
    "target",
    "tdd-summary",
}


def maintained_files() -> list[Path]:
    """Return project files that carry maintained product identity."""
    return [
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file() and not EXCLUDED_PARTS.intersection(path.relative_to(PROJECT_ROOT).parts)
    ]


def test_new_python_package_and_cli_identity() -> None:
    package = importlib.import_module("bangumi_renamer")
    cli = importlib.import_module("bangumi_renamer.cli")

    result = CliRunner().invoke(cli.app, ["--version"])

    assert package.__version__ == "0.1.0"
    assert result.exit_code == 0
    assert "bangumi-renamer 0.1.0" in result.stdout


def test_maintained_files_have_no_legacy_identity() -> None:
    offenders: list[str] = []
    for path in maintained_files():
        relative = path.relative_to(PROJECT_ROOT)
        if LEGACY_NAME in relative.as_posix().casefold():
            offenders.append(str(relative))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if LEGACY_NAME in content.casefold():
            offenders.append(str(relative))

    assert offenders == []
