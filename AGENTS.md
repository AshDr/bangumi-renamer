# Repository Guidelines

## Project Structure & Module Organization
This repository uses a `src/` layout. Core application code lives in `src/minifilebot/`, with CLI entrypoints in `cli.py`, shared rename pipeline logic in `core.py`, TMDB access in `tmdb.py`, and desktop GUI code under `src/minifilebot/gui/`. Tests live in `tests/`, with GUI coverage in `tests/gui/` and shared fixtures in `tests/conftest.py` and `tests/fixtures/`. Runtime artifacts such as rename history are written to `.minifilebot/` and must not be committed.

## Build, Test, and Development Commands
Use `uv` for all Python workflows.

```bash
uv sync --extra dev --extra gui   # Install app, test, lint, and GUI dependencies
uv run pytest -v                  # Run the full test suite
uv run pytest tests/gui -v        # Run GUI-focused tests
uv run ruff check src tests       # Lint project code
uv run minifilebot /path/to/media # Run CLI in dry-run mode
uv run minifilebot-gui            # Launch the PySide6 GUI
```

Python 3.11+ is required. Keep local secrets in `.env`; never commit TMDB keys.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, type hints, and a `src/minifilebot/` import root. Ruff is configured with a 100-character line length and enforces `E`, `F`, `I`, `B`, `UP`, `N`, and `SIM` rules. Use `snake_case` for functions, variables, and module names; use `PascalCase` for classes. Keep comments and documentation in English, and prefer small, composable functions over deeply stateful logic.

## Testing Guidelines
Tests use `pytest`, `pytest-qt`, and `respx`. Add unit tests beside the affected domain module, using `tests/test_<module>.py`; GUI regressions belong in `tests/gui/test_<feature>.py`. Cover both dry-run planning and applied rename behavior when changing the pipeline. Run `uv run pytest -v` before opening a PR, and add focused regression tests for bug fixes.

## Commit & Pull Request Guidelines
This repository currently has no commit history, so no project-specific commit convention exists yet. Use short, imperative commit subjects such as `Add TMDB cache expiry test` or `Fix GUI candidate selection`. Keep commits scoped to a single change. PRs should include a concise summary, testing notes, linked issues if applicable, and screenshots or terminal output when changing CLI or GUI behavior.

## Security & Configuration Tips
TMDB credentials may come from `TMDB_API_KEY` or GUI settings. Treat `.env` and local app settings as sensitive. Do not commit `.minifilebot/`, caches, virtual environments, or generated coverage output.
