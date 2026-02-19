---
phase: 02-build-deploy
plan: 01
subsystem: infra
tags: [pyinstaller, powershell, build, versioning, bom-import-tool]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: __version__ in scripts/main.py and working bom-import-tool.spec
provides:
  - scripts/build.ps1 — single command to produce versioned exe from source
affects:
  - 02-02 (deploy script needs dist/bom-import-tool.exe and versioned filename)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Version sourced from __version__ in main.py — single source of truth for versioning"
    - "Build script produces both bom-import-tool-{version}.exe (versioned) and bom-import-tool.exe (alias)"

key-files:
  created:
    - scripts/build.ps1
  modified: []

key-decisions:
  - "Build script uses Push-Location/Pop-Location to run pyinstaller from scripts/ dir (spec uses relative paths)"
  - "Both versioned exe and base alias kept: versioned for traceability, alias for deploy script compatibility"
  - "ErrorActionPreference = Stop ensures any failure exits cleanly without silent errors"

patterns-established:
  - "Pre-flight checks before expensive operations (spec exists, pyinstaller available)"
  - "Version extraction via regex match on __version__ = 'X.Y.Z' pattern"

# Metrics
duration: 8min
completed: 2026-02-19
---

# Phase 2 Plan 01: Build Script Summary

**PowerShell build script that extracts __version__ from main.py and runs PyInstaller to produce dist/bom-import-tool-1.0.0.exe alongside a stable bom-import-tool.exe alias**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-19T12:25:49Z
- **Completed:** 2026-02-19T12:33:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Build script reads version dynamically from `main.py` — changing `__version__` automatically updates the next build filename
- Pre-flight checks guard against missing spec file and missing PyInstaller before running
- Both versioned (`bom-import-tool-1.0.0.exe`) and base alias (`bom-import-tool.exe`) produced for deploy script compatibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Create build.ps1 — versioned PyInstaller build script** - `b691de3` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `scripts/build.ps1` - PowerShell build script: reads version, pre-flight checks, runs pyinstaller --clean --noconfirm, renames output

## Decisions Made
- `Push-Location`/`Pop-Location` used to change to `scripts/` directory before running PyInstaller — the spec file uses relative paths and requires being run from that directory
- Both `bom-import-tool-{version}.exe` (copy) and `bom-import-tool.exe` (original) kept in dist — versioned for traceability, alias for deploy script to use without needing to know the version

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `scripts/build.ps1` is ready; deploy script (02-02) can reference `dist/bom-import-tool.exe` or `dist/bom-import-tool-{version}.exe`
- PyInstaller must be installed in the Python environment for build to succeed (`pip install pyinstaller`)

## Self-Check: PASSED

- FOUND: scripts/build.ps1
- FOUND commit: b691de3 (feat(02-01): create versioned PyInstaller build script)
- Version extraction verified: outputs "Version: 1.0.0" from main.py

---
*Phase: 02-build-deploy*
*Completed: 2026-02-19*
