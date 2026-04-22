# MiniFileBot - Requirements Document

## 1. Overview

### 1.1 Project Name

MiniFileBot (Phase 1 + Phase 2)

### 1.2 Objective

Build a tool that:

- Parses anime / TV episode filenames
- Matches metadata via the TMDB API
- Renames files using a standardized format, safely (dry-run by default)

The tool ships with both a Typer CLI (`minifilebot`) and a PySide6 desktop
GUI (`minifilebot-gui`). They share the same core pipeline (`minifilebot.core`).

---

## 2. Scope

### Included

- Single / batch file processing (recursive directory scan)
- TV series (anime-focused)
- TMDB metadata matching with fuzzy scoring + year tiebreaker
- Manual TMDB id override (`--tmdb-id` on CLI / right-click picker in GUI)
  for when auto-match is wrong
- File renaming (no moving)
- Dry-run by default, explicit confirmation required before writing to disk
- Local cache for TMDB responses (7-day TTL)
- Apply-journal under `.minifilebot/history/` for future undo support
- PySide6 desktop GUI: drag-drop folder, preview table, apply flow,
  settings persistence, manual candidate picker

### Excluded

- Subtitle download
- Directory reorganisation (moving files between folders)
- Multiple metadata sources (TVDB, AniDB, Bangumi)
- Custom rename templates
- `undo` subcommand (history file is written but reverse not implemented yet)
- Packaged binaries (.app / .exe); Phase 2 ships as `uv run` scripts only

---

## 3. Input / Output

### Input

```bash
minifilebot /path/to/videos
```

### Example Inputs

```
[SubsPlease] Frieren - 01 (1080p).mkv
Attack.on.Titan.S04E01.1080p.mkv
Jujutsu Kaisen 2nd Season - 05.mkv
```

### Output Format

```
{SeriesName} - S{season:02}E{episode:02} - {EpisodeTitle}.{ext}
```

### Example Outputs

```
Frieren - S01E01 - The Journey's End.mkv
Attack on Titan - S04E01 - The Other Side of the Sea.mkv
```

---

## 4. Core Modules

### 4.1 Filename Parser

Extract: title, season, episode, release group, extension.

Implementation: [`anitopy`](https://github.com/igorcmoura/anitopy) wrapper with
a small post-processing layer that:

- Collapses `.` / `_` to spaces and normalises whitespace
- Defaults missing season to `1` (or `0` when anitopy tags the file as SP/OVA)
- Rejects files where title or episode cannot be extracted
- Guards against the occasional `anitopy` internal crash on pathological names

### 4.2 TMDB Matching

Steps:

1. Search `/search/tv` by parsed title (cached)
2. Score each candidate with `rapidfuzz.token_set_ratio` against both `name`
   and `original_name`; take the max
3. Add +15 bonus when `first_air_date` year is within +/-1 of a hint year
4. Reject the best candidate if its score is below `60`; otherwise return
   `{tmdb_id, name, confidence, reason}`

Override: `--tmdb-id <N>` bypasses step 1-4 entirely. The id is validated
via `/tv/{id}` and used for every file in the run.

### 4.3 Episode Lookup

`/tv/{id}/season/{season}` is fetched once per `(tmdb_id, season)` and cached
in-process as well as on disk. Episode titles come from the resulting list.

### 4.4 Renaming

Template:

```
{SeriesName} - S{season:02}E{episode:02} - {EpisodeTitle}.{ext}
```

Safety rules:

- Strip Windows-illegal characters (`< > : " / \ | ? *`) and control chars
- Unicode NFC normalisation
- Trim trailing dots and spaces (Windows breaks on these)
- Clamp final name to 240 bytes of stem + extension to stay under the 255-byte
  filesystem limit on all mainstream FSes
- Conflict policy (configurable via `--on-conflict`):
  `suffix` (default, appends ` (1)`), `skip`, or `overwrite`

### 4.5 Batch Processing

- Recursive scan of the input directory
- Filters for `.mkv / .mp4 / .avi / .m4v / .mov`
- Skips hidden files and the `.minifilebot/` working directory

---

## 5. Architecture

```
Front-ends         shared pipeline                    I/O
---------          ----------------                   ----
CLI  (Typer)   \   Scanner    directory walk
                \  Parser     anitopy + normalisation
GUI (PySide6)  --> Matcher    rapidfuzz scoring --->  TMDB (httpx + JSON
                /             (search_candidates /                disk cache,
                /              match / force_match)             7d TTL)
                   Core.build_plan / apply_plan
                   Renamer    template + sanitise + conflicts
                   History    .minifilebot/history/<ts>.json
```

Both front-ends call the same ``minifilebot.core`` module, so behaviour is
guaranteed identical. The GUI adds a ``QThread``-based worker layer so TMDB
network I/O does not block the event loop.

---

## 6. Error Handling

| Situation | Behaviour |
|-----------|-----------|
| Cannot parse filename | Row marked `unparsed`; rest of batch continues |
| No TMDB results or best score < threshold | Row marked `no match` |
| Target filename already exists | Depends on `--on-conflict`; default suffixes ` (1)` |
| TMDB HTTP/transport error | Row marked `error` with the message |
| Missing `TMDB_API_KEY` | CLI exits `2` with a clear message before any work |
| User declines confirmation on `--apply` | CLI exits `1`, nothing renamed |

The executor never raises out of a single-file failure - all files in a batch
are reported together in the summary table.

---

## 7. Configuration

Environment variables:

```
TMDB_API_KEY=xxxx
```

Flags (see README for full details): `--apply`, `--tmdb-id`, `--lang`,
`--yes`, `--on-conflict`, `--verbose`.

---

## 8. Acceptance Criteria

- Parse success rate >= 70% on a realistic sample (covered by
  `tests/fixtures/filenames.txt`, 30 samples)
- TMDB API integration works (exercised end-to-end with respx mocks in
  `tests/test_cli.py`; live smoke test documented in README)
- Correct renaming matches the template
- Batch processing supported
- No unhandled exceptions - every failure is a row with a status, not a crash

---

## 9. Tech Stack

- Python 3.11+, managed with `uv`
- `typer` + `rich` (CLI + preview tables)
- `anitopy` (filename parser)
- `rapidfuzz` (match scoring)
- `httpx` (TMDB client) + `platformdirs` (cache dir)
- `pytest` + `respx` (offline TMDB mocks)

---

## 10. Next Steps (future phases)

- `undo` subcommand that reads history files
- Multi-source metadata (TVDB, AniDB, Bangumi)
- Subtitle download integration
- Packaged GUI binaries (.app on macOS, .exe on Windows) via PyInstaller
- Custom rename templates and per-directory config
- Editable target cells in the GUI table

---

## 11. GUI (Phase 2)

### 11.1 Goals

- First-class experience for non-terminal users
- CLI parity: everything the CLI can do, the GUI can do
- Manual override beyond ``--tmdb-id``: let the user pick from a ranked
  TMDB candidate list when auto-match is wrong or ambiguous

### 11.2 Windows and flows

| Component | Purpose |
|-----------|---------|
| ``MainWindow`` | Toolbar, menu, drag-drop area, preview table, status bar |
| ``PlanModel`` | ``QAbstractTableModel`` wrapping ``list[PlanItem]`` |
| ``PlanView`` | ``QTableView`` with right-click "Pick different match..." |
| ``SettingsDialog`` | TMDB API key (password echo) / language / conflict policy |
| ``CandidateDialog`` | Scored TMDB candidates with overview, double-click to accept |
| ``ScanWorker`` / ``ApplyWorker`` / ``CandidateFetchWorker`` / ``RebuildWorker`` | ``QThread`` workers so TMDB I/O never blocks the UI |

### 11.3 UX rules

- Default dry-run: scan a folder, show the plan, never write until the user
  clicks Apply AND confirms a modal dialog.
- All TMDB network I/O runs on a worker thread.
- API key resolution order: ``$TMDB_API_KEY`` > ``QSettings`` > prompt.
  First run with no key shows the Settings dialog automatically.
- API key is stored with password echo and masked in any error messages.
- Right-click on any row -> "Pick different match..." opens the candidate
  dialog. Picking an entry re-resolves every row whose parsed title matches,
  not just the clicked one.

### 11.4 Entry points

- CLI: ``uv run minifilebot <path>``
- GUI: ``uv run minifilebot-gui`` (requires ``uv sync --extra gui``)

### 11.5 Acceptance criteria

- ``uv run minifilebot-gui`` opens the main window without error.
- Dropping a folder populates the preview table with correct status colours.
- Apply renames the files on disk and writes the history journal.
- Right-clicking a "no season" row and picking a different TMDB entry
  updates that row to OK with the new series name and episode title.
- Closing the window while a worker is running does not crash the process.
