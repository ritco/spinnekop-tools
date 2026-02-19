---
phase: 03-stable-release
plan: 01
subsystem: infra
tags: [powershell, deploy, promote, archive, release-pipeline]

# Dependency graph
requires:
  - phase: 02-build-deploy
    provides: deploy.ps1 patterns, Y:/Z: drive setup, server share layout
provides:
  - scripts/promote.ps1 — one-command promote from dev to stable with archive safety net
affects: [release workflow, evy-shortcut, server-stable-channel]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Promote pattern: archive-before-overwrite for safe rollback"
    - "Idempotent drive mapping reused from deploy.ps1"
    - "Semi-auto confirmation gate before destructive operation"

key-files:
  created:
    - scripts/promote.ps1
  modified: []

key-decisions:
  - "Both Z: and Y: drives are REQUIRED for promote (unlike deploy.ps1 where Z: was optional)"
  - "Archive path uses version string: Z:\\archive\\{version}\\ — human-readable rollback history"
  - "First-ever promote (no existing stable) is handled gracefully — archive step skipped with informational message"
  - "File size comparison as lightweight integrity check after copy"

patterns-established:
  - "Promote safety: always archive before overwrite"
  - "Step numbering [N/6] matches deploy.ps1 style [N/4]"

# Metrics
duration: 2min
completed: 2026-02-19
---

# Phase 3 Plan 01: Promote Script Summary

**promote.ps1: one-command release pipeline that archives current stable to Z:\archive\{version}\ then promotes dev build from Y: to Z:, with confirmation gate and file size verification**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-19T11:59:14Z
- **Completed:** 2026-02-19T12:00:50Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint)
- **Files modified:** 1

## Accomplishments

- promote.ps1 created following exact patterns from deploy.ps1 (Dutch text, colored output, idempotent drive mapping)
- Archive-before-overwrite safety: Z:\archive\{version}\ created before stable is replaced
- Semi-auto confirmation prompt prevents accidental promotes
- Graceful first-promote handling (no existing stable = skip archive, continue)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create promote.ps1** - `5657a25` (feat)

**Plan metadata:** pending (after checkpoint verification)

## Files Created/Modified

- `scripts/promote.ps1` — 6-step promote script: version read, confirmation, VPN check, drive mapping, archive+promote, verification

## Decisions Made

- Both Z: and Y: drives required (fail-fast if either unavailable) — unlike deploy.ps1 where Z: was optional, promote needs both
- Archive path: `Z:\archive\{version}\bom-import-tool.exe` — versioned, human-readable
- File size check as lightweight post-copy integrity verification
- `$archiveCreated` flag controls whether archive line appears in final summary output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Task 2 (human-verify checkpoint) is pending — Rik needs to run promote.ps1 end-to-end on VMSERVERRUM to confirm:
1. Confirmation prompt works, "n" aborts cleanly
2. Archive is created at Z:\archive\{version}\
3. Z:\bom-import-tool.exe replaced with dev build
4. Evy's desktop shortcut opens the promoted version

---
*Phase: 03-stable-release*
*Completed: 2026-02-19 (partial — Task 2 checkpoint pending)*
