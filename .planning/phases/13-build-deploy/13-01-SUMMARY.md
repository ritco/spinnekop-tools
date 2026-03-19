---
phase: 13-build-deploy
plan: "01"
subsystem: eplan-import-tool
tags: [pyinstaller, deploy, powershell, release-pipeline]
dependency_graph:
  requires: []
  provides: [eplan-import-tool.spec, install-live.ps1, install-test.ps1, deploy/eplan/README.md]
  affects: [workflows/tool-release-pipeline.md]
tech_stack:
  added: []
  patterns: [PyInstaller one-file build, PSScriptRoot relative paths, Test-Connection ping-check]
key_files:
  created:
    - scripts/eplan-import-tool.spec
    - scripts/deploy/eplan/install-live.ps1
    - scripts/deploy/eplan/install-test.ps1
    - scripts/deploy/eplan/README.md
  modified:
    - workflows/tool-release-pipeline.md
decisions:
  - "hiddenimports beperkt tot 5 modules: customtkinter, eplan_gui, eplan_converter, history, app_config"
  - "Geen GitHub Actions workflow aangemaakt: release pipeline is volledig manueel via gh CLI"
  - "Test-Connection gebruikt in plaats van ping.exe voor betrouwbaarheid in PowerShell"
metrics:
  duration: "~2 min"
  completed: "2026-03-19"
  tasks_completed: 3
  files_created: 4
  files_modified: 1
---

# Phase 13 Plan 01: Build Config Artefacten ePlan Import Tool Summary

**One-liner:** PyInstaller spec en PowerShell deploy scripts voor ePlan Import Tool — klaar voor directe build en release in Plan 02.

## What Was Built

### Task 1: eplan-import-tool.spec

PyInstaller build-definitie voor `eplan-import-tool.exe`, gebaseerd op de structuur van `bom-import-tool.spec`.

- **Entry point:** `eplan_main.py` (was `main.py` in BOM tool)
- **Exe naam:** `eplan-import-tool`
- **hiddenimports:** `customtkinter`, `eplan_gui`, `eplan_converter`, `history`, `app_config`
- BOM-specifieke modules verwijderd: `gui`, `bom_converter`, `validation_engine`, `sql_validator`, `audit_logger`
- Alle PyInstaller opties (debug, console, upx, strip, etc.) identiek aan bom-import-tool.spec

### Task 2: Deploy scripts in scripts/deploy/eplan/

Drie bestanden aangemaakt voor de deploy-workflow:

**install-live.ps1** — kopieert exe naar `\\10.0.1.5\import` (live server share Z:)
- Test-Connection ping-check op 10.0.1.5 voor VPN-verificatie
- Controleert dat lokale exe bestaat voor kopieer
- `$PSScriptRoot` relatieve paden: werkt vanuit elke locatie

**install-test.ps1** — identieke structuur, kopieert naar `\\10.0.1.5\import-test` (test share Y:)
- Zelfde ping-check en foutafhandeling
- SharePath wijst naar `import-test` in plaats van `import`

**README.md** — beknopt deploy-draaiboek:
- Build commando met PyInstaller
- Install commando's voor test en live share
- Voorbeeld `gh release create` commando voor eerste release
- Verwijzing naar volledige documentatie in tool-release-pipeline.md

### Task 3: tool-release-pipeline.md bijgewerkt

Twee uitbreidingen aan het bestaande document:

- **Bestaande tools tabel:** derde rij toegevoegd voor ePlan Import Tool (`eplan-import-tool.exe`, prefix `eplan-`, entry point `scripts/eplan_main.py`)
- **Naamconventies tabel:** twee rijen toegevoegd voor `eplan-v1.0.0` (stabiel) en `eplan-v1.0.0-test` (prerelease)

## Commits

| Task | Commit | Beschrijving |
|------|--------|--------------|
| Task 1 | d408c91 | feat(13-01): add eplan-import-tool.spec voor PyInstaller build |
| Task 2 | 32a8c85 | feat(13-01): add ePlan deploy scripts met ping-check |
| Task 3 | 9d80dc6 | feat(13-01): voeg ePlan Import Tool toe aan tool-release-pipeline.md |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

- [x] `scripts/eplan-import-tool.spec` bestaat en bevat `eplan_main.py` + `eplan-import-tool`
- [x] `scripts/deploy/eplan/install-live.ps1` bestaat met Test-Connection ping-check
- [x] `scripts/deploy/eplan/install-test.ps1` bestaat met import-test share
- [x] `scripts/deploy/eplan/README.md` bestaat
- [x] `workflows/tool-release-pipeline.md` bevat `eplan-import-tool.exe` en `eplan_main.py`
- [x] Commits d408c91, 32a8c85, 9d80dc6 bestaan

## Self-Check: PASSED
