<div align="center">
  <img src="desktop/src-tauri/icons/icon.png" alt="Bangumi Renamer icon" width="160">
  <h1>Bangumi Renamer</h1>
  <p><a href="README.zh-CN.md">简体中文</a> | English</p>
</div>

A FileBot-style tool that renames anime and TV episode files using metadata from
[TheTVDB](https://thetvdb.com/) or
[The Movie Database (TMDB)](https://www.themoviedb.org/). It ships as both a Typer CLI and a
Tauri 2 desktop application with a React 18 frontend.

The desktop application supports both metadata providers and uses TheTVDB by default. The CLI
currently uses TMDB only.

## Features

- Anime-aware filename parsing via [`anitopy`](https://github.com/igorcmoura/anitopy), including
  common Chinese, Japanese, and English season and episode markers
- Recursive scanning for MKV, MP4, AVI, M4V, and MOV videos
- External subtitle support for ASS, SSA, SRT, VTT, SUB, IDX, SUP, and MKS files
- Subtitle language and disposition suffix preservation, such as `.chs.ass`, `.cht.ass`, and
  `.zh-Hans.forced.srt`
- TheTVDB v4 and TMDB v3 metadata lookup in the desktop application, with a local 7-day cache
- Fuzzy title matching with [`rapidfuzz`](https://github.com/rapidfuzz/RapidFuzz)
- Manual correction when auto-match is wrong: `--tmdb-id <N>` in the CLI or the provider candidate
  picker in the desktop application
- Conflict policies for skipping, adding a numeric suffix, or overwriting an existing target
- Safe by default: the CLI performs a dry run and the desktop shows a non-destructive preview until
  an explicit Apply step
- Desktop interface languages: Simplified Chinese, Traditional Chinese, English, and Japanese
- Desktop light, dark, and system themes, plus per-folder metadata language selection

## Install

The CLI requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). Desktop development also
requires Node.js 20+, the Rust toolchain, and the platform prerequisites for Tauri 2.

```bash
git clone https://github.com/AshDr/bangumi-renamer.git
cd bangumi-renamer
uv sync                    # CLI and Python core
uv sync --extra dev        # Python development dependencies
cd desktop && npm install  # React and Tauri dependencies
```

## Metadata credentials

The CLI currently requires a TMDB v3 API key:

```bash
export TMDB_API_KEY=your_key_here
```

You can get a key from <https://www.themoviedb.org/settings/api>. If you prefer a local `.env`
file, copy `.env.example` and explicitly ask `uv` to load it:

```bash
cp .env.example .env
uv run --env-file .env bangumi-renamer /path/to/videos
```

The desktop application supports these providers:

| Provider | Desktop credentials | Notes |
|----------|---------------------|-------|
| TheTVDB | `THETVDB_API_KEY`, with optional `THETVDB_PIN` | Default provider; uses the v4 API. A PIN may be required for subscriber-supported keys. |
| TMDB | `TMDB_API_KEY` | Optional alternative; uses the v3 API. |

Credentials can be entered in the desktop Settings dialog or supplied through the environment
variables shown above. See [TheTVDB API access](https://thetvdb.com/api-information) and
[TMDB API settings](https://www.themoviedb.org/settings/api) for provider-specific access terms.

## Usage - CLI

Dry-run preview (default, no files touched):

```bash
uv run bangumi-renamer /path/to/videos
```

Actually rename the files:

```bash
uv run bangumi-renamer /path/to/videos --apply
```

Force a specific TMDB TV ID when auto-match is wrong:

```bash
uv run bangumi-renamer /path/to/videos --tmdb-id 209867
```

Flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--version` | off | Print the CLI version and exit. |
| `--apply` | off | Perform the rename. Without it, only a preview is printed. |
| `--tmdb-id N` | auto | Skip search and matching; use this TMDB TV ID for every file. |
| `--lang` | `en-US` | TMDB metadata language. |
| `--yes` / `-y` | off | Skip the interactive y/N confirmation before `--apply`. |
| `--plain` | off | Emit stable tab-separated output for scripts. |
| `--json` | off | Emit structured JSON output. |
| `--no-color` | off | Disable ANSI colors in terminal output. |
| `--no-input` | off | Disable prompts; fail instead of asking for confirmation. |
| `--debug` | off | Show tracebacks for unexpected errors. |
| `--on-conflict` | `suffix` | Handle existing targets with `skip`, `suffix`, or `overwrite`. |
| `--verbose` / `-v` | off | Include additional parsing details. |

The path may be a single supported media file or a directory. Directory scans are recursive and
skip hidden files and directories. When stdout is not a TTY, the CLI automatically switches to
plain line-based output.

## Usage - Desktop application

```bash
cd desktop
npm run tauri dev
```

1. On first launch, Settings opens if the default TheTVDB provider has no API key. Select TheTVDB
   or TMDB and enter the corresponding credentials.
2. Drop a folder onto the window or use **Choose folder**. The application recursively scans it and
   builds a preview without changing any files.
3. Review the parsed season and episode, provider match, confidence, target name, and status. Change
   the metadata language for the current folder or use the search action to select another match.
4. Choose the target conflict policy in Settings. The default adds a numeric suffix.
5. Click **Apply**, then confirm the dialog. A history journal is written to
   `.bangumi-renamer/history/<timestamp>.json` under the selected root.

The React frontend never renames files itself. Tauri forwards allow-listed commands to
`bangumi_renamer.desktop_bridge`, which calls the same `build_plan()` and `apply_plan()` functions
used by the CLI.

To build an installable desktop bundle:

```bash
cd desktop
npm run tauri:build
```

The build script uses PyInstaller to create a one-file Python sidecar, then packages it with the
Tauri application.

## Output format

```text
{SeriesName}-S{season:02}E{episode:02}.{ext}
```

Example:

```text
[SubsPlease] Frieren - 01 (1080p).mkv
-> Frieren-S01E01.mkv
```

External subtitles use the same compact name while retaining recognized subtitle suffixes:

```text
[SubsPlease] Frieren - 01 (1080p).zh-Hans.forced.srt
-> Frieren-S01E01.zh-hans.forced.srt
```

## Project structure

```text
src/bangumi_renamer/
  cli.py             # Typer entry point
  core.py            # Shared build_plan / apply_plan pipeline
  scanner.py         # Recursive media discovery
  parser.py          # anitopy wrapper and subtitle suffix parsing
  metadata.py        # Shared metadata provider protocol
  thetvdb.py         # TheTVDB v4 client
  tmdb.py            # TMDB v3 client
  cache.py           # Local JSON TTL cache
  matcher.py         # rapidfuzz scoring and manual matching
  renamer.py         # Filename generation, sanitization, and conflict handling
  display.py         # Rich and plain CLI output
  history.py         # Apply journal under .bangumi-renamer/history/
  desktop_bridge.py  # Validated JSON bridge to the shared Python pipeline
desktop/
  src/               # React 18 and TypeScript frontend
  src-tauri/         # Tauri 2 and Rust desktop shell
scripts/
  build_desktop_bridge.py  # Builds the bundled Python sidecar
tests/
  test_*.py          # Python unit and integration tests
  scenario/          # Cross-component regression tests
```

## Development

```bash
uv sync --extra dev --extra desktop
uv run pytest -v
uv run ruff check src tests
cd desktop
npm install
npm run test
npm run build
```

## License

MIT

Metadata provided by [TheTVDB](https://thetvdb.com/). Please consider adding missing information
or subscribing.
