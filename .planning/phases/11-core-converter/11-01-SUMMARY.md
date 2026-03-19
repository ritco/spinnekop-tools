---
phase: 11-core-converter
plan: "01"
subsystem: eplan-converter
tags: [eplan, converter, excel-parser, sql-matching, ridderiq]
dependency_graph:
  requires: [scripts/app_config.py]
  provides: [scripts/eplan_converter.py]
  affects: [phase-12-gui]
tech_stack:
  added: [openpyxl]
  patterns: [dataclass, headless-module, lazy-import-fallback]
key_files:
  created:
    - scripts/eplan_converter.py
  modified: []
decisions:
  - "Vaste posities rij 4/6/7 voor ePlan Excel — geen auto-detectie, sneller en robuuster"
  - "Import-fallback: try app_config direct, except voeg scripts/ toe aan sys.path"
  - "Lokale teller voor 26xxx codes: haal MAX eenmalig op vóór de lus, verhoog per nieuw artikel"
  - "match_components ontvangt conn als parameter — caller is verantwoordelijk voor lifecycle"
metrics:
  duration: "~5 min"
  completed_date: "2026-03-19"
  tasks_completed: 2
  files_created: 1
  files_modified: 0
---

# Phase 11 Plan 01: Core Converter — Datamodel, Parser en SQL-matching

Headless ePlan converter module met Excel-parser, deduplicatie-aggregatie, en SQL-matchinglogica. Klaar als fundament voor Phase 12 GUI.

## What Was Built

`scripts/eplan_converter.py` (629 lijnen) met:

- `EplanRow` en `ConversionResult` dataclasses — gestructureerd resultaatobject
- `parse_eplan_excel()` — leest ePlan stuklijsten op vaste posities (rij 4 = projectnaam, rij 6 = headers, rij 7+ = data), kolommen op naam
- `aggregate_rows()` — dedupliceert op bestelnummer (case-insensitief), sommeert hoeveelheden
- `_extract_zoekterm()` — splitst bestelnummer op eerste punt (`SE.GV2ME08` → `GV2ME08`)
- `match_components()` — SQL matching op `R_ITEM.OMSCHRIJVING LIKE '%zoekterm%'`, 3-weg resultaat (0/1/2+ matches)
- `get_next_26xxx_code()` — MAX query + lokale teller voor unieke codes per run
- `write_output()` — 3 CSV bestanden identiek aan bom_converter.py structuur
- `convert()` — hoofd interface met dry_run=True/False

Getest op `20-analyse/Inputdocumenten/Stuklijst.xlsx` (9 rijen, 8 unieke componenten na aggregatie).

## Verification Results

- `parse_eplan_excel()` geeft `projectnaam='Sautrelle_2_2kw'`, 9 rijen
- `aggregate_rows()` geeft 8 unieke componenten (1 duplicaat samengevoegd)
- `_extract_zoekterm('SE.GV2ME08')` == `('GV2ME08', True)` — correct
- `_extract_zoekterm('GV2ME08')` == `('GV2ME08', False)` — correct, geen punt
- `match_components(rijen, None)` geeft blokkerende fout met "VPN" in tekst
- `convert()` zonder VPN geeft blokkerende fout, geen unhandled exception

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Import-fallback voor app_config**
- **Found during:** Task 1 verification
- **Issue:** `from scripts.eplan_converter import ...` vanuit project-root faalde omdat `from app_config import ...` de `scripts/` map niet op sys.path had
- **Fix:** try/except import-fallback: probeert `from app_config import ...` direct, valt terug op `sys.path.insert(0, Path(__file__).parent)` als dat mislukt
- **Files modified:** scripts/eplan_converter.py
- **Commit:** 1a169e2 (deel van initieel commit)

**2. [Scope] Task 1 en Task 2 in één commit**
- **Reden:** Alle functies (parse + match + convert) werden in één keer geschreven als coherente module. Geen aparte commits per taak — het bestand werkte pas compleet na alle functies.

## Commits

| Commit | Task | Description |
|--------|------|-------------|
| 1a169e2 | Task 1 + 2 | feat(11-01): ConversionResult dataclass, Excel-parser, SQL-matching en convert() interface |

## Self-Check: PASSED

- scripts/eplan_converter.py: FOUND
- commit 1a169e2: FOUND
