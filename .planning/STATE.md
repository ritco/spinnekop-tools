# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** Francis kan per project (VO) zien wat het aan uren en aankoop heeft gekost — zonder in het ERP te moeten duiken.
**Current focus:** Phase 14 — DB + Infrastructuur (v4.0 Rapporterings-DB)

## Current Position

Phase: 14 of 18 (DB + Infrastructuur)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-03-19 — Completed 12-02-PLAN.md — eplan_main.py entry point voor ePlan Import Tool

Note: v3.0 ePlan Import Tool (Phases 11-13) — Phase 12 fully completed (12-01 GUI + 12-02 entry point). Phase 13 (Build & Deploy) is next.

Progress: [Phase 14 ░░░░░░] [Phase 15 ░░░░░░] [Phase 16 ░░░░░░] [Phase 17 ░░░░░░] [Phase 18 ░░░░░░]

## Performance Metrics

**Velocity:**
- Total plans completed: 13 (v1.0: 5, v1.1: 5, v2.0: 3)
- Average duration: ~28 min
- Total execution time: ~4.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| v1.0 (1-3) | 5 | ~55 min | ~11 min |
| v1.1 (4-6) | 5 | ~222 min | ~44 min |

**Recent Trend:**
- Stable (complexity-adjusted)

| Phase 11 P01 | 5 min | 2 tasks | 1 file |
| Phase 11 P02 | 8 min | 2 tasks | 1 file |
| Phase 12 P01 | 2 min | 2 tasks | 1 file |
| Phase 12-gui P02 | 5 | 2 tasks | 1 files |
| Phase 13-build-deploy P01 | 2 | 3 tasks | 5 files |
| Phase 13-build-deploy P02 | 5 | 1 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v4.0]: Python + pyodbc + pandas stack — geen SSIS, ADF of nieuwe tooling
- [v4.0]: Three-layer medallion (raw/core/report) op dezelfde SQL Server instantie
- [v4.0]: Power BI Import mode (niet DirectQuery) — VPN onbetrouwbaar, productie-DB beschermen
- [v4.0]: ETL idempotency (DELETE today + re-insert) verplicht vanaf dag 1
- [v4.0]: fact_aankoop uitgesteld naar Phase 18 — inkoop FK-keten eerst bevestigen
- [v3.0]: ePlan tool volgt exact hetzelfde CTk patroon als gui.py
- [v3.0]: Output: 3 bestanden (01-nieuwe-artikelen-eplan.csv, 02-stuklijst-header.csv, 03-stuklijstregels.sql)
- [Phase 11]: Import-fallback voor app_config: try direct, except sys.path.insert scripts/
- [Phase 11]: Lokale 26xxx teller: MAX query eenmalig voor de lus, teller verhogen per nieuw artikel
- [Phase 11-core-converter]: Header-constanten als module-level exports (ARTIKEL_HEADERS etc.) zodat test-scripts en de GUI ze kunnen importeren zonder write_output te moeten aanroepen
- [Phase 11-core-converter]: Duplicaatcheck opent een tweede connectie na match_components omdat conn al gesloten is in de finally-block van stap 4
- [Phase 12-gui]: AnalysisFrame heeft geen on_kmb parameter — ePlan Import Tool heeft geen KMB stap (anders dan BOM Import Tool)
- [Phase 12-gui]: eplan_main.py volgt exact het main.py patroon — tool-naam 'eplan-import-tool', log 'eplan-update-debug.log'
- [Phase 13-build-deploy]: hiddenimports beperkt tot 5 modules: customtkinter, eplan_gui, eplan_converter, history, app_config
- [Phase 13-build-deploy]: PyInstaller build geslaagd zonder extra hiddenimports — de 5 modules uit spec waren voldoende
- [Phase 13-build-deploy]: GitHub release tag eplan-v1.0.0 — prefix eplan- correct voor auto-update filter in app_config

### Roadmap Evolution

- Phase 10 completed: BOM Import Tool — SQL Server Audit Log + GitHub Release Pipeline (2026-03-18)
- Phases 11-13 added: v3.0 ePlan Import Tool (2026-03-18)
- Phases 14-18 added: v4.0 Rapporterings-DB (2026-03-19)

### Pending Todos

- Plan Phase 14: run `/gsd:plan-phase 14`

### Blockers/Concerns

- [Phase 15]: VPN drops zijn gedocumenteerde realiteit — ETL-04 (pyodbc.pooling=False + ping check) verplicht voor eerste echte run
- [Phase 18]: FK-keten `inkoopfactuur → R_SALESORDER` onbevestigd — INKOOP-01 exploratie nodig voor Phase 18 kan worden gepland; idealiter doen tijdens Phase 14-15 bouwperiode
- [Phase 17]: Power BI Service vereist Pro-licentie + gateway — bevestig bij Lebon IT voor web-dashboards worden beloofd aan Francis/Carl; pilot blijft .pbix via Teams

## Session Continuity

Last session: 2026-03-19
Stopped at: Completed 12-02-PLAN.md — eplan_main.py entry point (v1.0.0, update-check thread, EplanApp mainloop)
Resume file: None
