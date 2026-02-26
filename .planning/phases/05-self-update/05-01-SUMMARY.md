---
phase: 05-self-update
plan: 01
subsystem: tooling
tags: [self-update, threading, customtkinter, ctk, bom-import-tool, app_config]

# Dependency graph
requires:
  - phase: 04-promote-v120-version-json
    provides: version.json op Z: share als single source of truth voor stable versies
provides:
  - check_for_update() met threading-based 2s timeout (geen hang bij onbereikbare share)
  - show_update_dialog() als CTk-gestylde modal dialog met Updaten/Later knoppen
  - do_self_update() met correcte batch via cd /d en move /y
  - main.py _check_update() integreert CTk dialog ipv tkinter messagebox
affects:
  - productiestructuur tool (als die ook self-update krijgt)

# Tech tracking
tech-stack:
  added: [threading (stdlib)]
  patterns:
    - Threading-based timeout voor UNC pad access (thread + Event + wait)
    - Lazy import van customtkinter in dialoogfuncties
    - Verborgen CTk root als parent voor CTkToplevel dialogs voor opstart

key-files:
  created: []
  modified:
    - scripts/app_config.py
    - scripts/main.py

key-decisions:
  - "Threading-based timeout ipv asyncio voor UNC access (eenvoudiger, geen event loop vereist)"
  - "Lazy import van customtkinter in show_update_dialog (consistent met show_settings_dialog)"
  - "Verborgen CTk root in _check_update() als parent voor CTkToplevel (CTkToplevel vereist CTk root)"
  - "move /y ipv del + ren in batch voor atomaire exe-swap"

patterns-established:
  - "Threading timeout pattern: thread + Event.set() in thread + Event.wait(timeout) in caller"
  - "CTk dialoogfunctie: CTkToplevel + grab_set() + wait_window() + result via lijst"

requirements-completed: [UPD-01, UPD-02, UPD-03, UPD-04]

# Metrics
duration: 12min
completed: 2026-02-26
---

# Phase 5 Plan 01: Self-Update Hardening Summary

**Threading-based timeout voor UNC share access, CTk-gestylde update dialog met Updaten/Later knoppen, en atomaire exe-swap via move /y in batch script**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-26T09:13:28Z
- **Completed:** 2026-02-26T09:15:31Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- check_for_update() retourneert binnen 2 seconden bij onbereikbare share via threading timeout
- show_update_dialog() is een CTk-gestylde modal dialog met versienummers en Updaten/Later knoppen (groen/grijs)
- do_self_update() genereert een _update.bat met cd /d en move /y voor correcte atomaire exe-swap
- main.py _check_update() gebruikt CTk dialog, geen tkinter messagebox meer

## Task Commits

Elke task atomair gecommit:

1. **Task 1: Harden check_for_update met timeout en CTk update dialog in app_config.py** - `b78f0c4` (feat)
2. **Task 2: Integreer CTk update dialog in main.py, verwijder tkinter messagebox** - `8763477` (feat)

**Plan metadata:** (docs commit volgt)

## Files Created/Modified

- `scripts/app_config.py` - Nieuw: `_read_version_json_with_timeout()`, `show_update_dialog()`. Gewijzigd: `check_for_update()` (timeout helper), `do_self_update()` (batch fix: cd /d + move /y)
- `scripts/main.py` - Gewijzigd: `_check_update()` gebruikt `show_update_dialog()` ipv `messagebox.askyesno`

## Decisions Made

- **Threading ipv asyncio voor timeout:** `threading.Thread` + `threading.Event` is eenvoudiger dan een asyncio event loop opzetten voor een eenmalige I/O operatie bij opstart. Geen extra dependencies.
- **Lazy import customtkinter in show_update_dialog:** Consistent met het patroon van `show_settings_dialog`. Vermijdt import-fouten als customtkinter niet aanwezig is in CLI-builds.
- **Verborgen CTk root in _check_update():** `CTkToplevel` vereist een actieve CTk applicatie als parent. Omdat `_check_update()` voor `App()` wordt aangeroepen, is een tijdelijke verborgen root nodig.
- **move /y ipv del + ren:** `move /y` is atomischer: overschrijft het doel in 1 OS-operatie. `del` + `ren` kan falen als de oude exe nog tijdelijk gelockt is na afsluiten.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - geen externe configuratie vereist. Self-update werkt automatisch wanneer de tool op het Spinnekop-netwerk is en een update beschikbaar is op de share.

## Next Phase Readiness

- Self-update mechaniek productie-klaar: betrouwbaar timeout, gestylde dialog, correcte exe-swap
- Tool herbouwen (PyInstaller) en promoten naar Z: vereist voor Evy (zie fase 4 procedures)
- Productiestructuur tool kan desgewenst dezelfde update-patronen overnemen

## Self-Check: PASSED

- FOUND: scripts/app_config.py
- FOUND: scripts/main.py
- FOUND: .planning/phases/05-self-update/05-01-SUMMARY.md
- FOUND commit: b78f0c4 (Task 1)
- FOUND commit: 8763477 (Task 2)

---
*Phase: 05-self-update*
*Completed: 2026-02-26*
