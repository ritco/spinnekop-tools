---
phase: 03-stable-release
verified: 2026-02-19T12:30:00Z
status: passed
score: 5/5 must-haves verified
---

# Phase 3: Stable Release Verification Report

**Phase Goal:** Rik can promote the dev version to stable, and the previous stable is archived so a bad deploy can be recovered from
**Verified:** 2026-02-19
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | promote.ps1 archives current stable to Z:\archive\{version}\ before overwriting | VERIFIED | Lines 113-128: archiveDir set, New-Item creates dir, Copy-Item copies stable BEFORE line 134 overwrites |
| 2 | After promote, Z:\bom-import-tool.exe contains the dev build from Y:\ | VERIFIED | Lines 111-112 define devExe (Y:) and stableExe (Z:); line 134: Copy-Item devExe stableExe -Force |
| 3 | Evy desktop shortcut opens the newly promoted version without any action | VERIFIED | Shortcut points to C:\import\bom-import-tool.exe; promote replaces file in-place; confirmed by Rik in task 2 end-to-end test |
| 4 | Archive folder contains a dated/versioned copy of every previous stable build | VERIFIED | archiveDir = importDrive\archive\Version; each promote creates a new versioned subdirectory |
| 5 | Promote asks for confirmation before proceeding (semi-auto, not fully auto) | VERIFIED | Line 50: Read-Host 'Doorgaan? (j/n)'; line 51: if confirm -ine 'j' then exit 0 |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| scripts/promote.ps1 | Promote command: archive old stable, copy dev to stable, verify | VERIFIED | Exists, 164 lines, substantive - all 6 steps implemented, Dutch language, colored output, no stubs |

**Artifact contains-checks (from PLAN must_haves):**

| Pattern | Line | Status |
|---------|------|--------|
| Test-Connection | 61 | FOUND |
| __version__ regex extraction | 31 | FOUND |
| Read-Host confirmation | 50 | FOUND |
| archive directory creation | 113, 125 | FOUND |
| Copy-Item archive operation | 126 | FOUND |
| Copy-Item promote operation | 134 | FOUND |
| ErrorActionPreference = Stop | 5 | FOUND |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| promote.ps1 | scripts/main.py | __version__ regex extraction | VERIFIED | Line 31 regex matches main.py line 11: __version__ = '1.0.0' |
| promote.ps1 | Z:\bom-import-tool.exe | Copy-Item from Y: to Z: | VERIFIED | Lines 111-112 set devExe/stableExe via exeName variable; line 134 executes copy. PLAN grep pattern did not match because variable indirection is used - correct PowerShell practice, not a gap |
| promote.ps1 | Z:\archive\{version}\bom-import-tool.exe | Copy-Item to archive before overwrite | VERIFIED | Lines 113 and 125-126: archiveDir constructed with version string, New-Item creates dir, Copy-Item archives old stable |

### Requirements Coverage

| Requirement | Phase | Status | Notes |
|-------------|-------|--------|-------|
| BLD-03: Promote command that copies dev to stable with archiving | 3 | SATISFIED | promote.ps1 implements full archive-before-overwrite promote workflow |
| RBK-01: Old stable moved to C:\import\archive\{versie}\ at promote | 3 | SATISFIED | Lines 113-128 implement exact behavior specified in requirement |

**Documentation note:** REQUIREMENTS.md traceability table shows BLD-03 and RBK-01 as Pending (unchecked). The implementation fully satisfies both requirements. The requirements file checkboxes need updating to [x] - documentation inconsistency only, not a deliverable gap.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| - | None found | - | - |

Scanned scripts/promote.ps1 for: TODO, FIXME, XXX, HACK, PLACEHOLDER, return null, empty handlers, placeholder strings. None found.

### Human Verification

#### 1. Evy Desktop Shortcut

**Test:** Open BOM Import Tool shortcut on VMSERVERRUM Public Desktop via RDP after a promote
**Expected:** Tool opens showing the promoted version number in the title bar
**Why human:** Cannot verify shortcut target or GUI title bar content programmatically from outside the server

**Evidence already on file:** SUMMARY documents Rik confirmed this during task 2 end-to-end test:
- Archive created: Z:\archive\1.0.0\bom-import-tool.exe (26.5 MB)
- Z:\bom-import-tool.exe replaced with dev build (31.2 MB)
- Evy desktop shortcut opens the promoted version

Human verification is complete for the current v1.0.0 promote cycle.

---

## Verification Notes

**Key link grep pattern mismatch - not a gap:** The PLAN specified 'Copy-Item.*bom-import-tool\.exe' as the grep pattern for the Y:-to-Z: copy link. The script uses exeName = 'bom-import-tool.exe' (line 13) and executes Copy-Item via variable indirection (line 134). The grep pattern does not match literally, but the wiring is present and correct.

**REQUIREMENTS.md tracking inconsistency (informational):** BLD-03 and RBK-01 remain marked as unchecked in .planning/REQUIREMENTS.md. Implementation is complete and verified. The requirements file checkboxes need ticking.

---

_Verified: 2026-02-19_
_Verifier: Claude (gsd-verifier)_
