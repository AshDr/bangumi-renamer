# Repository Guidelines

## Project Focus
MiniFileBot is a FileBot-style renamer for anime and TV episode files. It ships both a Typer CLI and a Tauri 2 desktop application with a React frontend. Both front ends rely on the same planning and apply pipeline in `src/minifilebot/core.py`. Keep behavior aligned across CLI and desktop when changing parsing, matching, planning, conflict handling, or apply semantics.

## Project Structure & Ownership
The repository uses a `src/` layout with the import root at `src/minifilebot/`.

- `cli.py`: Typer entry point and Rich terminal output.
- `core.py`: shared `build_plan()` / `apply_plan()` orchestration used by CLI and GUI.
- `scanner.py`, `parser.py`: file discovery and anime-aware filename parsing.
- `matcher.py`, `tmdb.py`, `cache.py`: TMDB lookup, fuzzy matching, and local cache behavior.
- `renamer.py`, `history.py`, `display.py`: target filename generation, apply journal, and CLI rendering.
- `desktop_bridge.py`: validated JSON boundary between Tauri and the Python core.
- `desktop/src/`: React 18, TypeScript, Vite, Tailwind, Lucide, and Framer Motion frontend.
- `desktop/src-tauri/`: Tauri 2 Rust shell, capability configuration, and command allow-list.
- `tests/`: CLI and core tests.
- `tests/test_desktop_bridge.py`: desktop boundary and apply-safety tests.

Runtime artifacts are written to `.minifilebot/`. They are local state, not source files.

## Environment & Commands
Use `uv` for Python workflows. Python 3.11+ is required.

```bash
uv sync                    # install CLI dependencies
uv sync --extra dev
cd desktop && npm install
uv run pytest -v
uv run ruff check src tests
uv run minifilebot /path/to/media
uv run minifilebot /path/to/media --apply
cd desktop && npm run tauri dev
```

Prefer targeted test runs while iterating, then run the relevant broader suite before finishing.

## Coding Style
Follow the existing Python style:

- 4-space indentation.
- Type hints throughout.
- `snake_case` for functions, methods, variables, and modules.
- `PascalCase` for classes.
- Comments and documentation in English.

Ruff is configured in `pyproject.toml` with a 100-character line length and the `E`, `F`, `I`, `B`, `UP`, `N`, and `SIM` rule sets. Respect existing per-file ignores, especially for Typer defaults.

## Change Guidance
When changing rename logic, preserve the app's safe-by-default flow:

- Dry-run must remain the default for the CLI.
- Desktop preview must stay non-destructive until the user explicitly applies.
- `apply_plan()` should only rename files that are explicitly marked actionable.
- History output under `.minifilebot/history/` should remain consistent for applied operations.

When changing TMDB or matcher behavior, account for:

- forced matches via `--tmdb-id`
- per-title and per-season caching within plan building
- anime season mismatches where release tags and TMDB season numbering differ
- language-sensitive metadata fetched through `TmdbClient`

## Testing Expectations
Python tests use `pytest` and `respx`; frontend tests use Vitest.

- Add unit tests next to the affected module as `tests/test_<module>.py`.
- Add desktop bridge regressions in `tests/test_desktop_bridge.py` and frontend regressions next to the affected React module.
- For pipeline changes, cover both plan generation and applied rename behavior.
- For desktop changes, keep bridge tests independent of a real Tauri window and isolate platform settings paths.
- Prefer `tmp_path` and fixtures over real filesystem state or user settings.

## Repository Hygiene
Do not commit secrets or generated state.

- TMDB credentials may come from `.env`, `TMDB_API_KEY`, or GUI settings.
- Do not commit `.env`, `.env.local`, `.minifilebot/`, virtual environments, coverage output, or tool caches.
- Keep `git status` focused; if a new tool or workflow creates local artifacts, update `.gitignore` as part of the change.

## Commits & PRs
Use short, imperative commit subjects such as `Add conflict handling regression test` or `Fix GUI apply progress update`. Keep each commit scoped to one change. PRs should summarize user-visible behavior, list verification commands, and include screenshots or terminal output when CLI or GUI behavior changes.
