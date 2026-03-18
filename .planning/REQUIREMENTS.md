# Requirements: ePlan Import Tool (v3.0)

**Defined:** 2026-03-18
**Core Value:** Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## v1 Requirements

### Invoer & Parsing

- [ ] **PARSE-01**: Tool leest ePlan Excel exportbestand in het vaste formaat (projectnaam rij 4, headers rij 6: Naam in schema / Fabrikant / Bestelnummer / Hoeveelheid, data vanaf rij 7)
- [ ] **PARSE-02**: Tool aggregeert hoeveelheden van identieke Bestelnummers (zelfde component meerdere keren in schema → opgetelde qty in één stuklijstregel)
- [ ] **PARSE-03**: Rijen zonder Bestelnummer of Fabrikant worden overgeslagen met een waarschuwing (niet blokkerend)

### Matching

- [ ] **MATCH-01**: Voor elk Bestelnummer (format `Fabrikant.Onderdeel`) haalt de tool het Onderdeel-deel op en zoekt dit op in `R_ITEM.OMSCHRIJVING` via `LIKE '%Onderdeel%'`
- [ ] **MATCH-02**: Bij exact 1 match gebruikt de tool de bestaande RidderIQ artikelcode
- [ ] **MATCH-03**: Bij 0 matches maakt de tool een nieuw artikel aan (zie ART-01)
- [ ] **MATCH-04**: Bij meer dan 1 match toont de tool een blokkerende fout met de conflicterende artikelen

### Artikelen

- [ ] **ART-01**: Nieuwe artikelen krijgen een automatisch gegenereerde 26xxx code (`MAX(CODE) WHERE CODE LIKE '26%'` + 1), omschrijving = Bestelnummer, artikelgroep PK 673 (groep 26), eenheid stuks (FK 5), `REGISTRATIONPATH=5`, `INVENTORYKIND=4`
- [ ] **ART-02**: Nieuwe artikelen worden gegenereerd als CSV (`01-nieuwe-artikelen-eplan.csv`) voor R_ITEM import via RidderIQ importmodule

### Stuklijst

- [ ] **BOM-01**: Tool genereert stuklijstkop CSV (`02-stuklijst-header.csv`) voor R_ASSEMBLY import, met projectnaam uit ePlan Excel als stuklijstcode
- [ ] **BOM-02**: Tool genereert SQL script (`03-stuklijstregels.sql`) voor R_ASSEMBLYDETAILITEM INSERT met geaggregeerde hoeveelheden per component
- [ ] **BOM-03**: Als stuklijst met dezelfde code al bestaat in R_ASSEMBLY, toont de tool een blokkerende fout vóór import

### GUI

- [ ] **GUI-01**: Gebruiker kan ePlan Excel bestand selecteren via bestandsdialoog (StartFrame, zelfde patroon als gui.py)
- [ ] **GUI-02**: Gebruiker kiest importomgeving: Speeltuin of Live (via `app_config.py`)
- [ ] **GUI-03**: Validatieresultaten worden getoond per categorie: gevonden artikelen, nieuwe artikelen, overgeslagen rijen, blokkerende fouten (AnalysisFrame)
- [ ] **GUI-04**: Na goedkeuring genereert de tool outputbestanden (CSV + SQL) en toont stapsgewijze importinstructies

### Build & Deploy

- [ ] **BUILD-01**: Tool gebouwd als standalone exe via PyInstaller (`eplan-import-tool.exe`), entry point `scripts/eplan_main.py`
- [ ] **BUILD-02**: Tool volgt GitHub release pipeline: tag prefix `eplan-`, self-update via `app_config.check_for_update()`
- [ ] **BUILD-03**: Installatiescripts `install-live.ps1` en `install-test.ps1` in `scripts/deploy/eplan/`

## v2 Requirements

### Artikelverrijking

- **ART-V2-01**: Leverancier koppelen aan nieuw artikel (R_ITEMSUPPLIER) op basis van Fabrikant-code
- **ART-V2-02**: Inkoopprijs instellen op nieuw artikel (STANDARDPURCHASEPRICE)

### Stuklijst uitbreidingen

- **BOM-V2-01**: Bestaande stuklijst bijwerken (regels toevoegen/aanpassen) i.p.v. blokkeren

## Out of Scope

| Feature | Reason |
|---------|--------|
| Sub-assemblies in stuklijst | ePlan geeft platte lijst, geen hiërarchie |
| Bewerkingen (R_ASSEMBLYMISCWORKSTEP) | Elektro-componenten hebben geen bewerkingen |
| Leveranciers automatisch koppelen | Fabrikant-code → R_RELATION mapping ontbreekt nog (v2) |
| Automatisch afboeken (REGISTRATIONPATH=8) | Handmatig afboeken is huidige werkwijze voor elektro |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | TBD | Pending |
| PARSE-02 | TBD | Pending |
| PARSE-03 | TBD | Pending |
| MATCH-01 | TBD | Pending |
| MATCH-02 | TBD | Pending |
| MATCH-03 | TBD | Pending |
| MATCH-04 | TBD | Pending |
| ART-01 | TBD | Pending |
| ART-02 | TBD | Pending |
| BOM-01 | TBD | Pending |
| BOM-02 | TBD | Pending |
| BOM-03 | TBD | Pending |
| GUI-01 | TBD | Pending |
| GUI-02 | TBD | Pending |
| GUI-03 | TBD | Pending |
| GUI-04 | TBD | Pending |
| BUILD-01 | TBD | Pending |
| BUILD-02 | TBD | Pending |
| BUILD-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: TBD
- Unmapped: TBD

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after initial definition*
