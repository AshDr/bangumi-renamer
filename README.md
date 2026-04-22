# MiniFileBot

A FileBot-style tool that renames anime / TV episode files using metadata
from [The Movie Database](https://www.themoviedb.org/). Ships as both a CLI
and a PySide6 desktop GUI.

## Features

- Anime-aware filename parsing via [`anitopy`](https://github.com/igorcmoura/anitopy)
- TMDB metadata lookup with local cache (7-day TTL)
- Fuzzy matching with [`rapidfuzz`](https://github.com/rapidfuzz/RapidFuzz) and year disambiguation
- Manual override when auto-match is wrong: `--tmdb-id <N>` (CLI) or
  right-click "Pick different match..." (GUI)
- **Safe by default**: dry-run preview; nothing touches disk without an
  explicit Apply step
- CLI: Rich preview table; GUI: drag-drop folder, colour-coded status rows,
  modal candidate picker

## Install

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone <this-repo> OpenFileBot
cd OpenFileBot
uv sync                    # CLI only
uv sync --extra gui        # CLI + GUI (adds PySide6)
```

Set your TMDB API key:

```bash
cp .env.example .env
# edit .env and paste your key, or:
export TMDB_API_KEY=your_key_here
```

Get a key from <https://www.themoviedb.org/settings/api> (free, instant).

The GUI can also store the key in ``QSettings`` via **File -> Settings...**,
so you don't need the env var after first launch.

## Usage — CLI

Dry-run preview (default, no files touched):

```bash
uv run minifilebot /path/to/videos
```

Actually rename the files:

```bash
uv run minifilebot /path/to/videos --apply
```

Force a specific TMDB TV id when auto-match is wrong:

```bash
uv run minifilebot /path/to/videos --tmdb-id 209867
```

Flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--apply` | off | Perform the rename. Without it, only a preview table is printed. |
| `--tmdb-id N` | auto | Skip search + matcher; use this TV id for every file. |
| `--lang` | `en-US` | TMDB metadata language. |
| `--yes` / `-y` | off | Skip the interactive y/N confirmation before `--apply`. |
| `--verbose` / `-v` | off | Verbose logging. |

## Usage — GUI

```bash
uv run minifilebot-gui
```

1. First launch: the Settings dialog asks for your TMDB API key.
2. Drop a folder onto the window (or use **File -> Open Folder...**). The
   preview table fills in automatically; nothing is written yet.
3. If a row shows `no match` or `no season`, right-click it and choose
   **Pick different match...** to select from the TMDB candidate list.
4. Click **Apply** in the toolbar, confirm the dialog, and the files are
   renamed on disk. A history journal is written to
   `.minifilebot/history/<timestamp>.json`.

Keyboard shortcuts: ``Ctrl+O`` Open Folder, ``Ctrl+R`` Rescan,
``Ctrl+Return`` Apply, ``Ctrl+,`` Settings.

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
src/minifilebot/
  cli.py        # Typer entry point
  core.py       # Shared pipeline: build_plan / apply_plan
  scanner.py    # Directory traversal
  parser.py     # anitopy wrapper -> ParsedFile
  tmdb.py       # httpx TMDB client
  cache.py      # JSON TTL cache
  matcher.py    # rapidfuzz scoring + search_candidates / force_match
  renamer.py    # Template + filename sanitisation + conflict handling
  display.py    # Rich preview table (CLI only)
  history.py    # Apply journal at .minifilebot/history/
  gui/          # PySide6 desktop GUI
    main.py           # minifilebot-gui entry point
    main_window.py    # Toolbar + drag-drop + preview table
    plan_model.py     # QAbstractTableModel over PlanItem list
    plan_view.py      # QTableView with right-click menu
    candidate_dialog.py  # "Pick different match" picker
    settings_dialog.py   # API key / lang / conflict policy
    worker.py           # QThread wrappers for scan / apply / rebuild
tests/
  test_*.py     # Core + CLI tests (pytest + respx)
  gui/          # PySide6 smoke tests (pytest-qt, offscreen Qt platform)
```

## Development

```bash
uv sync --extra dev --extra gui
uv run pytest -v
uv run ruff check src tests
```

## License

MIT
