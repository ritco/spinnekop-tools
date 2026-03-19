---
phase: 12-gui
plan: "01"
subsystem: eplan-gui
tags: [gui, customtkinter, eplan, import-tool]
dependency_graph:
  requires: [eplan_converter.convert, eplan_converter.ConversionResult, history.log_import, history.get_recent_display, app_config]
  provides: [scripts/eplan_gui.py, StartFrame, AnalysisFrame, EplanApp]
  affects: [scripts/eplan_main.py]
tech_stack:
  added: []
  patterns: [CustomTkinter CTk GUI, two-frame navigation pattern, dry_run two-step flow]
key_files:
  created: [scripts/eplan_gui.py]
  modified: []
decisions:
  - "No on_kmb parameter in AnalysisFrame — ePlan heeft geen KMB stap (anders dan BOM Import Tool)"
  - "btn_generate text updates dynamisch met waarschuwingsaantal bij warnings aanwezig"
  - "Importinstructies tonen Stap 1 conditioneel (alleen als result2.new_items niet leeg)"
metrics:
  duration: "2 min"
  completed: "2026-03-19"
  tasks_completed: 2
  files_created: 1
requirements: [GUI-01, GUI-02, GUI-03, GUI-04, HIST-01, HIST-02]
---

# Phase 12 Plan 01: ePlan GUI Summary

**One-liner:** CustomTkinter GUI voor ePlan Import Tool met twee-staps flow (dry_run analyse + output generatie), identiek patroon aan BOM Import Tool gui.py.

## What Was Built

`scripts/eplan_gui.py` — volledig werkend CustomTkinter GUI bestand met drie klassen:

- **StartFrame**: Blauw header-blok met APP_TITLE + versie, omgeving-selector (Speelomgeving/Live), "Open ePlan Excel" knop met .xlsx filter, recente imports sectie (tot 8 items), footer met gebruiker/basis info en instellingen-knop.

- **AnalysisFrame**: 5 samenvattingskaarten (Matched/Nieuw/Overgeslagen/Fouten/Waarschuwingen), status bar (groen/amber/rood afhankelijk van resultaat), scrollbare meldingen lijst met kleurgecodeerde rijen per fout/waarschuwing, "Genereer output" knop (uitgeschakeld bij `has_blockers=True`), "Annuleren" knop.

- **EplanApp**: Hoofdvenster 900x700, twee-staps flow (`dry_run=True` bij bestand laden, `dry_run=False` bij output genereren), `log_import()` na succesvolle generatie, `get_recent_display()` bij terugkeer naar StartFrame, stapsgewijze importinstructies met conditionele Stap 1 (alleen bij nieuwe artikelen).

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | StartFrame voor ePlan Import Tool | 668e79e | scripts/eplan_gui.py |
| 2 | AnalysisFrame en EplanApp met twee-staps flow | 668e79e | scripts/eplan_gui.py |

## Success Criteria Verification

- [x] `scripts/eplan_gui.py` bestaat en importeert zonder fouten
- [x] StartFrame toont omgeving-selector (speel/live), open-knop met .xlsx filter, recente imports
- [x] AnalysisFrame toont 5 samenvattingskaarten (matched, nieuw, overgeslagen, fouten, warnings)
- [x] `btn_generate` is uitgeschakeld bij `has_blockers`, ingeschakeld anders (GUI-03)
- [x] Twee-staps flow: `dry_run=True` bij openen, `dry_run=False` bij genereren (GUI-01, GUI-02)
- [x] `log_import` wordt aangeroepen na succesvolle output-generatie (HIST-01)
- [x] `get_recent_display()` wordt aangeroepen bij terugkeer naar StartFrame (HIST-02)
- [x] Importinstructies tonen stapsgewijze tekst: Stap 1 conditioneel, Stap 2 en 3 altijd (GUI-04)

## Deviations from Plan

None — plan executed exactly as written.

Tasks 1 and 2 committed together in a single commit (668e79e) because both tasks write to the same file and the file is only importable/testable as a complete unit.

## Self-Check: PASSED

- FOUND: scripts/eplan_gui.py (657 lines, exceeds min_lines: 300)
- FOUND: commit 668e79e
- Imports verified: StartFrame, AnalysisFrame, EplanApp all import without error
- Key links verified: `dry_run=True`, `dry_run=False`, `log_import`, `has_blockers` all present in source
- `show_results` signature: `['self', 'excel_path', 'omgeving', 'result']` — correct
