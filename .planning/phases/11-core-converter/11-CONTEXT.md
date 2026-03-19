# Phase 11: Core Converter - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Headless Python module `eplan_converter.py` — leest ePlan Excel export, matcht componenten in RidderIQ via SQL, en genereert maximaal 3 CSV-outputbestanden klaar voor RidderIQ importmodule. Geen GUI in deze fase. Geen directe SQL INSERT — alles via CSV import workflow.

</domain>

<decisions>
## Implementation Decisions

### Excel parsing
- Vaste posities: rij 4 = projectnaam, rij 6 = kolomheaders, rij 7+ = dataregels
- Kolommen matchen op naam (niet positie): zoek 'Fabrikant', 'Bestelnummer', 'Hoeveelheid', 'Naam in schema'
- Lege tussenrijen worden stilzwijgend overgeslagen
- Extra (onbekende) kolommen worden genegeerd — geen fout, geen waarschuwing

### Matching logica
- Bestelnummer format: `Fabrikant.Onderdeel` (bv. `SE.GV2ME08`) — splits op eerste punt, gebruik Onderdeel-deel als zoekterm
- Zoekopdracht: `LIKE '%Onderdeel%'` case-insensitief op `R_ITEM.OMSCHRIJVING`
- Fabrikant-prefix wordt NIET gebruikt in de zoekopdracht
- Geen punt in Bestelnummer → gebruik hele string als zoekterm + log een waarschuwing
- 0 matches → artikel aanmaken als nieuw (ART-01)
- 1 match → gebruik bestaande RidderIQ artikelcode
- 2+ matches → blokkerende fout, toon alle conflicterende artikelen

### Foutafhandeling
- **Aanpak**: verwerk alle rijen door, verzamel alle fouten — geen stop bij eerste fout
- **Blokkerend** (geen CSV output): match-ambiguiteit (2+ matches), stuklijst bestaat al in R_ASSEMBLY
- **Waarschuwend** (output wel gegenereerd): rijen zonder Bestelnummer of Fabrikant overgeslagen, Bestelnummer zonder punt
- **Return interface**: gestructureerd resultaat-object met velden `errors` (blokkerend), `warnings`, `matched`, `new_items`, `skipped` — GUI leest dit object
- **Geen connectie**: `ConnectionError` met duidelijke melding "Controleer VPN en serveradres" — geen half-gegenereerde output

### Output bestanden
- **Formaat**: alle output als CSV (geen SQL!) — puntkomma scheidingsteken, UTF-8-BOM encoding
- **3 bestanden**:
  - `01-nieuwe-artikelen-eplan.csv` — R_ITEM import (alleen als er nieuwe artikelen zijn)
  - `02-stuklijst-header.csv` — R_ASSEMBLY import (altijd)
  - `03-stuklijstregels.csv` — R_ASSEMBLYDETAILITEM import (altijd)
- **Alleen benodigde bestanden schrijven**: als er geen nieuwe artikelen zijn, wordt `01-nieuwe-artikelen-eplan.csv` niet aangemaakt
- **Output locatie**: instelbaar via `app_config.py` (OUTPUT_DIR in config.json) — consistent met BOM Import Tool
- **Twee-stappen aanpak**:
  - Stap 1: `convert(excel_path, db_config, dry_run=True)` — matching + validatie, geen bestanden geschreven, geeft resultaat-object terug
  - Stap 2: `convert(excel_path, db_config, dry_run=False)` — alleen als geen blockers — schrijft CSV bestanden
  - GUI roept stap 1 aan voor de analysefase, stap 2 na gebruikersgoedkeuring

### Claude's Discretion
- Interne klassestructuur van `ConversionResult` object
- SQL query optimalisatie (één query per component of batch)
- Logging naar console vs structureel
- Exacte CSV kolomvolgorde (volg R_ITEM importschema uit bestaande bom_converter.py)

</decisions>

<specifics>
## Specific Ideas

- **Identiek CSV formaat als BOM Import Tool** — exact dezelfde kolomheaders, volgorde en encoding. Eén RidderIQ importworkflow voor beide tools, geen aparte importschema's nodig.
  - `01-nieuwe-artikelen-eplan.csv` → zelfde kolommen als bestaande R_ITEM import CSV uit bom_converter.py
  - `02-stuklijst-header.csv` → zelfde kolommen als `02-stuklijst-headers.csv` uit BOM tool
  - `03-stuklijstregels.csv` → zelfde kolommen als `03-stuklijstregels.csv` uit BOM tool
- Gebruik `bom_converter.py` als directe referentie voor alle CSV-structuren — niet nabootsen maar exact overnemen
- Referentiebestand voor de Excel structuur: `20-analyse/Inputdocumenten/Stuklijst.xlsx`

</specifics>

<deferred>
## Deferred Ideas

- Geen deferred ideas — discussie bleef binnen Phase 11 scope

</deferred>

---

*Phase: 11-core-converter*
*Context gathered: 2026-03-18*
