---
phase: 06-productiestructuur-config-update
plan: 02
subsystem: tooling
tags: [phantom-tool, productiestructuur, build, deploy, self-update, pyinstaller, explorer-launch]

# Dependency graph
requires:
  - phase: 06-productiestructuur-config-update-01
    provides: phantom_tool.py v1.0.0 met config.json integratie en two-phase self-update
provides:
  - productiestructuur.exe v1.0.0 live op Z: met werkende config.json en self-update
  - Self-update DLL-fix in app_config.py (explorer launch ipv start "")
affects:
  - bom-import-tool self-update profiteert ook van de DLL-fix in gedeelde app_config.py

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "explorer.exe ipv start \"\" voor exe-launch na self-update: voorkomt PyInstaller python314.dll LoadLibrary failure"
    - "Unblock-File na shutil.copy2 van UNC share: verwijdert Zone.Identifier ADS"
    - "CREATE_NO_WINDOW voor batch, explorer voor GUI exe launch: gescheiden concerns"

key-files:
  created:
    - scripts/dist/productiestructuur.exe
  modified:
    - scripts/app_config.py

key-decisions:
  - "explorer.exe launch in _update.bat: lost 'Failed to load Python DLL' fout op die optrad bij start \"\" vanuit CREATE_NO_WINDOW context"
  - "Unblock-File als best-effort stap na copy: voorkomt Windows Defender blokkade op network-gekopieerde exe"
  - "Vast timeout (3s + 2s) behouden ipv PID-based wait: PID-check via tasklist werkt niet in CREATE_NO_WINDOW context"

patterns-established:
  - "Self-update launch via explorer ipv start: robuuster voor PyInstaller onefile windowed builds"
  - "Beide tools (bom-import-tool, productiestructuur) delen dezelfde do_self_update() in app_config.py"

requirements-completed: [PST-01, PST-02]

# Metrics
duration: ~90min (inclusief debugging DLL-fout en 3 rebuild cycles)
completed: 2026-02-26
---

# Phase 6 Plan 02: Build + Deploy + E2E Summary

**productiestructuur.exe v1.0.0 live op Z: — config.json, self-update en graceful fallback E2E bewezen**

## Performance

- **Duration:** ~90 min (inclusief DLL-fix debugging)
- **Started:** 2026-02-26T11:00:00Z
- **Completed:** 2026-02-26T13:00:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 2 (app_config.py, dist/productiestructuur.exe)

## Accomplishments

- productiestructuur.exe v1.0.0 gebuild en gedeployed naar Z: (stable)
- version.json op Z: bevat `"productiestructuur": "1.0.0"` naast bestaande `"bom-import-tool": "1.2.1"`
- E2E verificatie door gebruiker: alle 4 tests geslaagd
- **Critical bugfix**: "Failed to load Python DLL" fout opgelost in app_config.py do_self_update()

## E2E Test Results

| Test | Resultaat |
|------|-----------|
| 1. Settings dialog bij ontbrekende config.json | OK |
| 2. Normaal gebruik (ophalen, phantom toggles) | OK |
| 3. Self-update dialog + exe-swap + herstart | OK (na DLL-fix) |
| 4. Graceful fallback zonder netwerk | OK |

## Critical Bugfix: Python DLL Loading

**Probleem:** Na self-update via `_update.bat` faalde de nieuwe exe met:
```
Failed to load Python DLL 'C:\...\Temp\_MEI{random}\python314.dll'
LoadLibrary: The specified module could not be found.
```

**Root cause:** `start "" "{exe}"` vanuit een `CREATE_NO_WINDOW` batch context creëert geen proper geïnitialiseerd GUI-process. PyInstaller's windowed bootloader kan dan python314.dll niet laden uit de _MEI extractie-directory.

**Fix (3 onderdelen):**
1. `explorer "{local_exe}"` ipv `start "" "{local_exe}"` — Windows Shell lanceert de exe met correcte process-initialisatie
2. `Unblock-File` na `shutil.copy2` — verwijdert Zone.Identifier ADS van network-gekopieerde exe
3. `CREATE_NO_WINDOW` behouden voor batch (bewezen werkend), alleen de exe-launch via explorer

**Impact:** Fix zit in gedeelde `app_config.py` — beide tools profiteren automatisch.

## Task Commits

1. **Task 1: Build + deploy** — productiestructuur.exe v1.0.0 op Z:
2. **Task 2: E2E checkpoint** — gebruiker bevestigt 4/4 tests OK

## Files Created/Modified

- `scripts/app_config.py` — do_self_update(): explorer launch, Unblock-File, vast timeout 3s+2s
- `scripts/dist/productiestructuur.exe` — v1.0.0 final build

## Deviations from Plan

- Y: drive was locked (device busy) — direct naar Z: gedeployed ipv via promote.ps1
- Self-update test vereiste 3 rebuild cycles om DLL-fout te diagnosticeren en fixen
- app_config.py aangepast (niet in origineel plan) — noodzakelijk voor werkende self-update

## Issues Encountered

- **Python DLL LoadLibrary failure** — 3 pogingen nodig: (1) timeout verhogen hielp niet, (2) DETACHED_PROCESS brak batch executie, (3) explorer launch + Unblock-File loste het op
- **Y: drive locked** — omzeild door direct naar Z: te deployen

## Next Phase Readiness

- Milestone v1.1 is feature-complete: beide tools draaien met config.json en self-update
- Klaar voor milestone-afsluiting en optioneel: handmatige installatie op Jurgens laptop door Rik

## Self-Check: PASSED

- Z:/productiestructuur.exe: exists, v1.0.0
- Z:/version.json: `{"bom-import-tool": "1.2.1", "productiestructuur": "1.0.0"}`
- E2E: 4/4 tests goedgekeurd door gebruiker
- DLL-fix in app_config.py gedeeld door beide tools

---
*Phase: 06-productiestructuur-config-update*
*Completed: 2026-02-26*
