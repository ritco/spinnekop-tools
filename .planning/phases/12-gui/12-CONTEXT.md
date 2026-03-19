# Phase 12: GUI - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

CustomTkinter GUI voor de ePlan Import Tool — Florian en Toby kunnen een ePlan Excel selecteren, de analyse bekijken, en outputbestanden genereren zonder commandoregel. Bouwt op eplan_converter.py (Phase 11).

</domain>

<decisions>
## Implementation Decisions

### Gebruikers
- **Florian en Toby** — niet Evy (eerder foutief vermeld)
- Zelfde niveau als BOM Import Tool gebruikers — vertrouwd met de import workflow

### GUI patroon
- Exact hetzelfde patroon als gui.py (BOM Import Tool): StartFrame + AnalysisFrame
- CustomTkinter, zelfde styling en lay-out als bestaande tool
- Nieuw bestand: scripts/eplan_gui.py + scripts/eplan_main.py

### Claude's Discretion
- Exacte lay-out binnen CTk conventies
- Kleurkeuzes (volg bestaande gui.py)
- Foutmelding teksten

</decisions>

<specifics>
## Specific Ideas

- Referentie: scripts/gui.py — zelfde structuur, zelfde patroon, zelfde gebruikerservaring
- Omgeving-selector (Speeltuin / Live) via app_config.py
- Importinstructies na output generatie: stapsgewijs (zelfde stijl als BOM tool)

</specifics>

<deferred>
## Deferred Ideas

- Geen deferred ideas

</deferred>

---

*Phase: 12-gui*
*Context gathered: 2026-03-19*
