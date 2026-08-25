# Bangumi Renamer - Requirements Document

## 1. Overview

### 1.1 Project Name

Bangumi Renamer (Phase 1 + Phase 2)

### 1.2 Objective

Build a tool that:

- Parses anime / TV episode filenames
- Matches metadata via the TMDB API
- Renames files using a standardized format, safely (dry-run by default)

The tool ships with both a Typer CLI (`bangumi-renamer`) and a Tauri 2 desktop
application with a React 18 frontend. They share the same Python core pipeline
(`bangumi_renamer.core`).

---

## 2. Scope

### Included

- Single / batch file processing (recursive directory scan)
- TV series (anime-focused)
- TMDB metadata matching with fuzzy scoring + year tiebreaker
- Manual TMDB id override (`--tmdb-id` on CLI / candidate picker on desktop)
  for when auto-match is wrong
- File renaming (no moving)
- Dry-run by default, explicit confirmation required before writing to disk
- Local cache for TMDB responses (7-day TTL)
- Apply-journal under `.bangumi-renamer/history/` for future undo support
- Tauri desktop application: drag-drop folder, plan dashboard, apply flow,
  settings persistence, manual candidate picker, and animated transitions

### Excluded

- Subtitle download
- Directory reorganisation (moving files between folders)
- Multiple metadata sources (TVDB, AniDB, Bangumi)
- Custom rename templates
- `undo` subcommand (history file is written but reverse not implemented yet)
- Signed and notarized release artifacts

---

## 3. Input / Output

### Input

```bash
bangumi-renamer /path/to/videos
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
- Skips hidden files and the `.bangumi-renamer/` working directory

---

## 5. Architecture

```
Frontends                desktop boundary             shared Python pipeline
---------                ----------------             ----------------------
CLI (Typer) ---------------------------------------> Core.build_plan/apply_plan

React 18 + TypeScript -> Tauri 2 allow-list -> JSON bridge -> Scanner / Parser
       |                   (Rust)                           -> Matcher / TMDB
       +-- Vite / Tailwind / Lucide / Framer Motion        -> Renamer / History
```

Both frontends call the same ``bangumi_renamer.core`` module. Tauri runs the Python
bridge outside the WebView, so TMDB and filesystem operations never block the
React event loop. Release builds bundle that bridge as a PyInstaller sidecar.

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
- Tauri 2 + Rust (desktop shell and command allow-list)
- React 18 + TypeScript + Vite 7 (desktop UI)
- Tailwind CSS + Lucide React + Framer Motion (visual system)
- Vitest (frontend unit tests)

---

## 10. Next Steps (future phases)

- `undo` subcommand that reads history files
- Multi-source metadata (TVDB, AniDB, Bangumi)
- Subtitle download integration
- Signed and notarized desktop releases
- Custom rename templates and per-directory config
- Editable target cells in the GUI table

---

## 11. Desktop Application (Phase 2)

### 11.1 Goals

- First-class experience for non-terminal users
- CLI parity: everything the CLI can do, the desktop application can do
- Manual override beyond ``--tmdb-id``: let the user pick from a ranked
  TMDB candidate list when auto-match is wrong or ambiguous

### 11.2 Windows and flows

| Component | Purpose |
|-----------|---------|
| ``App`` | Workflow sidebar, folder drop area, preview table, summaries, and apply bar |
| ``SettingsModal`` | TMDB API key, language, and conflict policy |
| ``CandidateModal`` | Ranked TMDB candidates with confidence and overview |
| ``desktopApi`` | Typed frontend API with a non-destructive browser preview adapter |
| ``execute_bridge`` | Tauri command that only accepts allow-listed operations |
| ``desktop_bridge`` | Validates JSON payloads and calls the shared Python pipeline |

### 11.3 UX rules

- Default dry-run: scan a folder, show the plan, never write until the user
  clicks Apply AND confirms a modal dialog.
- All TMDB and filesystem I/O runs outside the WebView.
- API key resolution order: ``$TMDB_API_KEY`` > platform settings file > prompt.
  First run with no key shows the Settings dialog automatically.
- API key is stored with password echo and masked in any error messages.
- The search action on any parsed row opens the candidate dialog. Picking an
  entry re-resolves every row whose parsed title matches,
  not just the clicked one.

### 11.4 Entry points

- CLI: ``uv run bangumi-renamer <path>``
- Desktop development: ``cd desktop && npm run tauri dev``
- Desktop package: ``cd desktop && npm run tauri:build``

### 11.5 Acceptance criteria

- ``npm run tauri dev`` opens the main window without error.
- Dropping a folder populates the preview table with correct status colours.
- Apply renames the files on disk and writes the history journal.
- Opening a "no season" row and picking a different TMDB entry
  updates that row to OK with the new series name and episode title.
- Closing the window while a bridge command is running does not corrupt files.
