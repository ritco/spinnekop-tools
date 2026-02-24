---
phase: 01-foundation
plan: 01
subsystem: ui
tags: [python, customtkinter, gui, versioning]

# Dependency graph
requires: []
provides:
  - "__version__ = '1.0.0' in main.py as single source of truth for version number"
  - "Dynamic title bar in App showing version and active environment"
  - "on_env_changed callback pattern in StartFrame for real-time title updates"
affects: [01-02, 01-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-source-of-truth version via __version__, callback injection for UI state propagation]

key-files:
  created: []
  modified:
    - scripts/main.py
    - scripts/gui.py

key-decisions:
  - "__version__ placed after module docstring, before imports — importable without circular dependency risk"
  - "on_env_changed callback injected into StartFrame rather than polling — avoids tight coupling between StartFrame and App"
  - "Title format: 'BOM Import Tool v{version} [{omgeving_label}]' — version and environment always visible"

patterns-established:
  - "Version pattern: __version__ in main.py, imported as APP_VERSION = __version__ in gui.py"
  - "Callback pattern: UI state changes bubble up via injected callbacks (on_env_changed)"

# Metrics
duration: 9min
completed: 2026-02-19
---

# Phase 1 Plan 01: Versioning Summary

**Single-source __version__ in main.py with dynamic title bar showing "BOM Import Tool v1.0.0 [Speelomgeving/Live]" that updates in real-time when the user switches environment**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-19T10:37:44Z
- **Completed:** 2026-02-19T10:46:24Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `__version__ = '1.0.0'` added to `main.py` after module docstring — clean single source of truth
- `gui.py` now derives `APP_VERSION = __version__` by importing from `main`
- Title bar formats as `"BOM Import Tool v1.0.0 [Speelomgeving]"` on startup
- `trace_add` on `omgeving_var` fires `_update_title` immediately when user toggles Speelomgeving / Live
- Title also updates when navigating to analysis screen and when returning to start screen

## Task Commits

Each task was committed atomically:

1. **Task 1: Voeg __version__ toe aan main.py** - `ac4ffae` (feat)
2. **Task 2: Update gui.py — importeer __version__, dynamische title bar met omgeving** - `8198747` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `scripts/main.py` - Added `__version__ = '1.0.0'` after module docstring, before imports
- `scripts/gui.py` - Added `from main import __version__`, `APP_VERSION = __version__`, `on_env_changed` parameter in `StartFrame`, `trace_add` on `omgeving_var`, `App._update_title()` method, title updates in `_show_start` and `_load_file`

## Decisions Made
- `__version__` placed after docstring but before imports: this is the Python convention and ensures it is importable without side effects
- `on_env_changed` injected as optional parameter to `StartFrame.__init__` rather than having `StartFrame` know about `App` — keeps the dependency direction clean
- `_update_title` called in three places: `App.__init__` (startup default), `_show_start` (when returning from analysis), and `_load_file` (after analysis shown) — ensures title is never stale

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. `python -m py_compile` returned a confusing exit code in the bash shell, but `python -c "import ast; ast.parse(...)"` confirmed syntax is valid.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Version infrastructure in place; plan 01-02 (server migration and shortcut) can proceed immediately
- `__version__` value will need to be bumped when a new release is built — that's deliberate manual work

---
*Phase: 01-foundation*
*Completed: 2026-02-19*

## Self-Check: PASSED

- FOUND: scripts/main.py
- FOUND: scripts/gui.py
- FOUND: .planning/phases/01-foundation/01-01-SUMMARY.md
- FOUND commit: ac4ffae (feat(01-01): add __version__ to main.py as single source of truth)
- FOUND commit: 8198747 (feat(01-01): dynamic title bar with version and environment in gui.py)
