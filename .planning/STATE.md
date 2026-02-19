# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-19)

**Core value:** Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.
**Current focus:** Phase 3 - Stable Release

## Current Position

Phase: 3 of 3 (Stable Release)
Plan: 1 of 1 in current phase — checkpoint pending (human-verify)
Status: Phase 3 in progress — promote.ps1 created, awaiting end-to-end verification
Last activity: 2026-02-19 — Plan 03-01 Task 1 complete (promote.ps1 created and committed)

Progress: [########░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: ~13min
- Total execution time: ~53min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 2/2 | ~30min | ~15min |
| 02-build-deploy | 2/2 | ~23min | ~12min |
| 03-stable-release | 0/1 + checkpoint | ~2min | — |

**Recent Trend:**
- Last 5 plans: 9min (01-01), ~20min (01-02), 8min (02-01), ~15min (02-02 incl. checkpoint)
- Trend: fast execution, checkpoints add ~5min overhead

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Semi-auto release: volledig geautomatiseerd is overkill, handmatig te foutgevoelig
- Stable/dev mappenstructuur: simpelste manier om Evy's versie te scheiden van dev builds
- __version__ na docstring vóór imports: importeerbaar zonder circulaire afhankelijkheden
- on_env_changed callback in StartFrame: UI state propageert omhoog via injection, niet via koppeling aan App
- Server mappenstructuur: C:\import\ (stable exe), C:\import-test\ (dev), C:\import\archive\ (vorige versies)
- Setup-scripts NIET als admin vereisen tenzij strict nodig
- Bash UNC paden werken niet → gebruik .ps1 temp files voor Z: drive operaties
- Build script: Push-Location/Pop-Location voor scripts/ directory (spec gebruikt relatieve paden)
- Build output: zowel bom-import-tool-{version}.exe (traceerbaar) als bom-import-tool.exe (alias voor deploy)
- Y: drive voor import-test share (Y: = test, Z: = productie import share)
- Z: mapping failure is non-blocking in deploy.ps1 (deploy vereist alleen Y:)
- promote.ps1: Z: EN Y: zijn beide REQUIRED (fail-fast als een van beide niet beschikbaar is)
- Archive pad: Z:\archive\{version}\ — versie-string als mapnaam voor menselijk leesbare rollback-historie

### Pending Todos

None yet.

### Blockers/Concerns

- VPN valt regelmatig weg: deploy scripts moeten robuust zijn met ping check voor elke Z: operatie
- Evy moet volgende week kunnen starten: Phase 2 + 3 moeten snel door

## Session Continuity

Last session: 2026-02-19
Stopped at: Phase 3, Plan 03-01 — Task 1 complete, checkpoint:human-verify pending (promote.ps1 end-to-end test)
Resume file: None
