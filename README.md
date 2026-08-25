# Bangumi Renamer

A FileBot-style tool that renames anime / TV episode files using metadata
from [The Movie Database](https://www.themoviedb.org/). Ships as both a Typer
CLI and a Tauri 2 desktop application with a React 18 frontend.

## Features

- Anime-aware filename parsing via [`anitopy`](https://github.com/igorcmoura/anitopy)
- TMDB metadata lookup with local cache (7-day TTL)
- Fuzzy matching with [`rapidfuzz`](https://github.com/rapidfuzz/RapidFuzz) and year disambiguation
- Manual override when auto-match is wrong: `--tmdb-id <N>` (CLI) or the
  candidate picker in the desktop application
- **Safe by default**: dry-run preview; nothing touches disk without an
  explicit Apply step
- CLI: Rich preview table; desktop: drag-drop folder, status dashboard,
  animated plan review, and modal candidate picker

## Install

The CLI requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). Desktop
development additionally requires Node.js 20+ and the Rust toolchain.

```bash
git clone <this-repo> bangumi-renamer
cd bangumi-renamer
uv sync                    # CLI only
uv sync --extra dev        # Python development dependencies
cd desktop && npm install  # React/Tauri frontend dependencies
```

Set your TMDB API key:

```bash
cp .env.example .env
# edit .env and paste your key, or:
export TMDB_API_KEY=your_key_here
```

Get a key from <https://www.themoviedb.org/settings/api> (free, instant).

The desktop application can store the key in the platform configuration
directory through its Settings panel, so the environment variable is optional.

## Usage — CLI

Dry-run preview (default, no files touched):

```bash
uv run bangumi-renamer /path/to/videos
```

Actually rename the files:

```bash
uv run bangumi-renamer /path/to/videos --apply
```

Force a specific TMDB TV id when auto-match is wrong:

```bash
uv run bangumi-renamer /path/to/videos --tmdb-id 209867
```

Flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--version` | off | Print the CLI version and exit. |
| `--apply` | off | Perform the rename. Without it, only a preview table is printed. |
| `--tmdb-id N` | auto | Skip search + matcher; use this TV id for every file. |
| `--lang` | `en-US` | TMDB metadata language. |
| `--yes` / `-y` | off | Skip the interactive y/N confirmation before `--apply`. |
| `--plain` | off | Emit stable tab-separated output for scripts. |
| `--json` | off | Emit structured JSON output. |
| `--no-color` | off | Disable ANSI colours in terminal output. |
| `--no-input` | off | Disable prompts; fail instead of asking for confirmation. |
| `--debug` | off | Show tracebacks for unexpected errors. |
| `--on-conflict` | `suffix` | Choose how existing targets are handled: `skip`, `suffix`, `overwrite`. |
| `--verbose` / `-v` | off | Verbose logging. |

When stdout is not a TTY, the CLI automatically switches to plain line-based output.

## Usage - Desktop application

```bash
cd desktop
npm run tauri dev
```

1. First launch: the Settings dialog asks for your TMDB API key.
2. Drop a folder onto the window or use **Choose folder**. The preview fills
   in automatically; nothing is written yet.
3. Use the search action on any parsed row to select a different TMDB match.
4. Click **Apply renames**, confirm the dialog, and the files are
   renamed on disk. A history journal is written to
   `.bangumi-renamer/history/<timestamp>.json`.

The React frontend never renames files itself. Tauri forwards allow-listed
commands to `bangumi_renamer.desktop_bridge`, which calls the same `build_plan()`
and `apply_plan()` functions used by the CLI.

To build an installable desktop bundle:

```bash
cd desktop
npm run tauri:build
```

This first builds a PyInstaller sidecar containing the Python core, then
packages that sidecar with the Tauri application.

## Output format

```
{SeriesName} - S{season:02}E{episode:02} - {EpisodeTitle}.{ext}
```

Example:

```
[SubsPlease] Frieren - 01 (1080p).mkv
-> Frieren - S01E01 - The Journey's End.mkv
```

## Project structure

```
src/bangumi_renamer/
  cli.py        # Typer entry point
  core.py       # Shared pipeline: build_plan / apply_plan
  scanner.py    # Directory traversal
  parser.py     # anitopy wrapper -> ParsedFile
  tmdb.py       # httpx TMDB client
  cache.py      # JSON TTL cache
  matcher.py    # rapidfuzz scoring + search_candidates / force_match
  renamer.py    # Template + filename sanitisation + conflict handling
  display.py    # Rich preview table (CLI only)
  history.py    # Apply journal at .bangumi-renamer/history/
  desktop_bridge.py  # Validated JSON bridge to the shared Python pipeline
desktop/
  src/          # React 18 + TypeScript frontend
  src-tauri/    # Tauri 2 / Rust desktop shell and command allow-list
scripts/
  build_desktop_bridge.py  # Builds the bundled Python sidecar
tests/
  test_*.py     # Core + CLI tests (pytest + respx)
  test_desktop_bridge.py  # Desktop boundary and apply-safety tests
```

## Development

```bash
uv sync --extra dev
uv run pytest -v
uv run ruff check src tests
cd desktop
npm run test
npm run build
```

## License

MIT
