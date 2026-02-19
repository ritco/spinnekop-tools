---
phase: 02-build-deploy
verified: 2026-02-19T13:00:00Z
status: passed
score: 7/7 must-haves verified
human_verification:
  - test: Run build.ps1 end-to-end
    expected: dist/bom-import-tool-1.0.0.exe appears alongside dist/bom-import-tool.exe
    why_human: Cannot run PyInstaller or verify the compiled output filename without executing the build
  - test: Run deploy.ps1 with VPN active
    expected: Script maps Y to import-test share and copies exe; final message shows deployed size and path
    why_human: VPN and server connectivity cannot be verified programmatically from this environment
  - test: Run deploy.ps1 with VPN disconnected
    expected: Script exits at step 2/4 with Dutch message - Server 10.0.1.5 niet bereikbaar. Check VPN verbinding.
    why_human: Cannot simulate VPN-down condition programmatically
---

# Phase 2: Build and Deploy Verification Report

**Phase Goal:** Rik can build a versioned exe and push it to the dev folder on the server with a single command sequence
**Verified:** 2026-02-19
**Status:** passed (with human verification items)
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | build.ps1 produces dist/bom-import-tool.exe from PyInstaller spec | VERIFIED | Line 45: pyinstaller --clean --noconfirm bom-import-tool.spec; dist/bom-import-tool.exe exists |
| 2 | Version from main.py __version__ embedded in filename as dist/bom-import-tool-{version}.exe | VERIFIED | Lines 57+65: VersionedExe constructed from Version var, Copy-Item BaseExe to VersionedExe; mechanism correct |
| 3 | Build fails cleanly if PyInstaller missing or spec file missing | VERIFIED | Lines 27-37: Test-Path spec and Get-Command pyinstaller each guard with Write-Error and exit 1 |
| 4 | deploy.ps1 copies exe to C:\import-test\ on VMSERVERRUM | VERIFIED | Line 22: exePath from PSScriptRoot\dist; line 98: Copy-Item -Force to Y:om-import-tool.exe |
| 5 | Deploy fails cleanly with clear message if server unreachable (VPN down) | VERIFIED | Lines 38-45: Test-Connection -Count 2 -Quiet; failure exits with Dutch message at step 2/4 |
| 6 | Deploy fails cleanly if no exe in dist/ (build not yet run) | VERIFIED | Lines 24-29: Test-Path guard with FOUT message and exit 1 |
| 7 | Rik can go from source change to testable exe on server in one command sequence | VERIFIED | Two-script pipeline build.ps1 then deploy.ps1; ROADMAP says command sequence, not single command |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| scripts/build.ps1 | Reads __version__, runs PyInstaller, renames output | VERIFIED | 69 lines; version regex, pre-flight checks, PyInstaller call, Copy-Item versioned rename |
| scripts/deploy.ps1 | Ping check, Y: drive mapping, copy to import-test | VERIFIED | 114 lines; Test-Connection, idempotent net use for Y: and Z:, Copy-Item, post-copy verification |
| scripts/main.py | Has __version__ = 1.0.0 (single source of truth) | VERIFIED | Line 11: __version__ = 1.0.0 - matches build.ps1 regex exactly |
| scripts/bom-import-tool.spec | PyInstaller spec (unchanged from Phase 1) | VERIFIED | 58 lines; build.ps1 references it via Join-Path ScriptDir |
| scripts/dist/bom-import-tool.exe | Base exe (alias kept by build.ps1) | VERIFIED | File exists; Phase 1 artifact; build.ps1 preserves it and adds versioned copy on each run |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| scripts/build.ps1 | scripts/main.py | regex parse of __version__ | WIRED | Line 19 regex pattern matches actual variable at main.py:11 |
| scripts/build.ps1 | scripts/bom-import-tool.spec | pyinstaller invocation with spec | WIRED | Line 45: pyinstaller --clean --noconfirm bom-import-tool.spec; spec existence checked at line 27 |
| scripts/deploy.ps1 | scripts/dist/bom-import-tool.exe | file copy source | WIRED | Line 22: exePath = Join-Path scriptDir dist\exeName; Copy-Item at line 98 |
| scripts/deploy.ps1 | .0.1.5\import-test | SMB Y: drive mapping | WIRED | Lines 67-91: net use Y: importTestShare; importTestShare set to .0.1.5\import-test |

### Requirements Coverage

| Requirement | Status | Notes |
| --- | --- | --- |
| BLD-01 | SATISFIED | build.ps1 reads __version__ from main.py, runs PyInstaller, produces versioned exe in dist/ |
| BLD-02 | SATISFIED | deploy.ps1 ping-checks before network ops, maps Y: to import-test, copies exe, verifies copy |

### Anti-Patterns Found

No anti-patterns found. Neither script contains TODO/FIXME/placeholder markers, stub implementations, or silent failure paths. All failure branches use exit 1 with explicit Dutch error messages.

### Human Verification Required

#### 1. Build end-to-end: versioned filename

**Test:** From project root, run: powershell -ExecutionPolicy Bypass -File scripts/build.ps1
**Expected:** Build completes, scripts/dist/bom-import-tool-1.0.0.exe appears alongside scripts/dist/bom-import-tool.exe, final line prints Build complete: dist/bom-import-tool-1.0.0.exe
**Why human:** Cannot run PyInstaller in this environment; cannot verify the versioned output filename is actually produced

#### 2. Deploy with VPN active

**Test:** With VPN connected and import-test share available, run: powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
**Expected:** Four steps print with status messages; final lines show Deploy geslaagd\! and exe path on VMSERVERRUM
**Why human:** VPN and server connectivity cannot be verified without an active network connection to 10.0.1.5

#### 3. Deploy with VPN disconnected (clean failure)

**Test:** Disconnect OpenVPN Connect, then run: powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
**Expected:** Script exits at step 2/4 within a few seconds, prints FOUT: Server 10.0.1.5 niet bereikbaar. Check VPN verbinding. with no hanging or cryptic errors
**Why human:** Cannot simulate VPN-down condition programmatically

### Gaps Summary

No gaps. All seven observable truths are verified by code inspection. Both scripts exist with full implementations - no stubs, no silent failures, no missing wiring.

Note: scripts/dist/bom-import-tool-1.0.0.exe does not yet exist in the repository, but this is a build artifact produced by running build.ps1 - not a source file. The script logic that produces it (lines 57 and 65 of build.ps1) is fully implemented and correct. The base scripts/dist/bom-import-tool.exe exists as the Phase 1 artifact and is the deploy source for deploy.ps1.

---

_Verified: 2026-02-19_
_Verifier: Claude (gsd-verifier)_