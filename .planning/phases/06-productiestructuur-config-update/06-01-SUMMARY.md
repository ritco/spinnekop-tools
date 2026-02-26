---
phase: 06-productiestructuur-config-update
plan: 01
subsystem: tooling
tags: [phantom-tool, productiestructuur, self-update, app_config, ctk, config-json, two-phase-update]

# Dependency graph
requires:
  - phase: 05-self-update-02
    provides: _check_update_before_gui() + _show_update_after_gui() patroon, _resolve_share() fallback, share_override parameter, encoding='utf-8-sig'
  - phase: 06-productiestructuur-config-update-01
    provides: app_config.py met check_for_update, do_self_update, show_update_dialog, config_exists, show_settings_dialog als tool-agnostische functies
provides:
  - phantom_tool.py v1.0.0 met config.json integratie en bewezen two-phase self-update
  - productiestructuur tool volgt identiek update-patroon als bom-import-tool
affects:
  - phase-06-02-build-deploy (build en promote van productiestructuur.exe v1.0.0)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-phase self-update in phantom_tool identiek aan main.py: _check_update_before_gui() voor App() init, _show_update_after_gui() na App() init
    - Top-level import van alle app_config functies (geen lazy imports meer in methoden)
    - share_override doorgegeven van _check_update_before_gui() naar _show_update_after_gui() via update_info dict

key-files:
  created: []
  modified:
    - scripts/phantom_tool.py

key-decisions:
  - "Two-phase patroon overgenomen van main.py zonder aanpassing: bewezen patroon vermijdt CTk dual-root crash"
  - "Top-level imports: alle app_config functies naar module-top verplaatst, lazy imports in __init__ en _open_settings verwijderd"
  - "app_config.py niet aangepast: functies zijn al tool-agnostisch met tool_name parameter"

patterns-established:
  - "phantom_tool update flow: check_for_update('productiestructuur', version) -> App() -> after(100, show_update_dialog)"
  - "Beide tools (bom-import-tool, productiestructuur) gebruiken exact hetzelfde two-phase patroon"

requirements-completed: [PST-01, PST-02]

# Metrics
duration: 7min
completed: 2026-02-26
---

# Phase 6 Plan 01: Productiestructuur Config Update Summary

**phantom_tool.py v1.0.0 met top-level app_config imports en bewezen two-phase self-update identiek aan bom-import-tool**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-02-26T10:57:10Z
- **Completed:** 2026-02-26T10:58:44Z
- **Tasks:** 1 (auto)
- **Files modified:** 1

## Accomplishments

- phantom_tool.py versie gebumped van 0.1.0 naar 1.0.0
- Titelbalk toont automatisch "Productiestructuur v1.0.0"
- Old `_check_update()` (tkinter.Tk root, messagebox) volledig verwijderd
- New `_check_update_before_gui()` + `_show_update_after_gui()` two-phase patroon geimplementeerd
- `main()` volgt exact hetzelfde patroon als bom-import-tool: check -> PhantomApp() -> after(100, dialog)
- share_override doorgegeven zodat resolved UNC/drive path hergebruikt wordt
- Alle app_config imports naar module-top verplaatst (schoner, geen dubbele lazy imports)
- config_exists() check in `__init__` en show_settings_dialog in `_open_settings` gebruiken nu top-level imports

## Task Commits

Elke task atomair gecommit:

1. **Task 1: Config integratie en self-update in phantom_tool.py** - `295b3d0` (feat)

**Plan metadata:** (docs commit volgt)

## Files Created/Modified

- `scripts/phantom_tool.py` - Versie 1.0.0; two-phase self-update via app_config; top-level imports; old _check_update() verwijderd

## Decisions Made

- Two-phase patroon letterlijk overgenomen van `main.py` — bewezen patroon, geen reden om af te wijken
- app_config.py niet aangepast — alle functies zijn al tool-agnostisch via `tool_name` parameter
- Top-level imports gekozen boven lazy imports: schoner en consistenter met rest van codebase

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - geen externe services. Tool werkt zodra config.json aanwezig is naast de exe.

## Next Phase Readiness

- phantom_tool.py v1.0.0 klaar voor build en promote (Phase 06-02)
- Self-update patroon is identiek aan bom-import-tool — Evy's laptop setup werkt ook voor productiestructuur
- version.json op Z: moet bijgewerkt worden met 'productiestructuur': '1.0.0' na promote

## Self-Check: PASSED

- FOUND: scripts/phantom_tool.py
- FOUND commit: 295b3d0 (Task 1)
- __version__ = '1.0.0' bevestigd via python verificatie
- _check_update_before_gui() en _show_update_after_gui() bestaan als top-level functies
- main() gebruikt two-phase patroon bevestigd via inspect.getsource()
- Oude _check_update() is verwijderd bevestigd via hasattr() check

---
*Phase: 06-productiestructuur-config-update*
*Completed: 2026-02-26*
