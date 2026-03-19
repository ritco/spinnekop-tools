# Requirements: Rapporterings-DB (v4.0)

**Defined:** 2026-03-19
**Core Value:** Francis kan per project (VO) zien wat het aan uren en aankoop heeft gekost — zonder in het ERP te moeten duiken.

## v1 Requirements — Fase 1: ETL Fundament + Uren Pilot

### Infrastructuur

- [ ] **INFRA-01**: Nieuwe database `Spinnekop_Reporting` aangemaakt op `10.0.1.5\RIDDERIQ` met drie schemas: `raw`, `core`, `report`
- [ ] **INFRA-02**: Alle DDL-scripts zijn idempotent (herhaalbaar zonder fouten op bestaande DB)
- [ ] **INFRA-03**: `dim_datum` kalender-tabel aanwezig in `core` (2020–2030, met week/maand/kwartaal/jaar kolommen)
- [ ] **INFRA-04**: ETL-controle tabel `raw.etl_log` aanwezig (run_date, tabel, rows_extracted, rows_loaded, status, error_msg)

### ETL — Extract

- [ ] **ETL-01**: Python extract-script kopieert nachtelijk `R_TIMESHEETLINE`, `R_PRODUCTIONORDER`, `R_SALESORDER`, `R_ITEM`, `R_EMPLOYEE` (of equivalent) naar `raw.*` tabellen
- [ ] **ETL-02**: Elke raw-tabel krijgt een `snapshot_date` kolom (datum van de run); rijen worden toegevoegd, nooit overschreven (append-only)
- [ ] **ETL-03**: Extract is idempotent: `DELETE WHERE snapshot_date = vandaag` vóór elke insert — geen dubbele rijen bij herstart
- [ ] **ETL-04**: `pyodbc.pooling = False` en expliciete connection timeout (5s) zodat VPN-drops geen hanging connections achterlaten
- [ ] **ETL-05**: Script logt elke run naar `raw.etl_log` met rowcounts en status (success/error)
- [ ] **ETL-06**: Script draait via Windows Task Scheduler (nachtelijk 02:00), met pingcheck op `10.0.1.5` vóór connectie

### ETL — Schema monitoring

- [ ] **ETL-07**: Script snapshort nachtelijk `INFORMATION_SCHEMA.COLUMNS` van de brondbases naar `raw.schema_snapshot` — vroege waarschuwing bij ERP-updates die kolomnamen wijzigen

### Core-laag — Dimensies

- [ ] **CORE-01**: `core.dim_verkooporder` aangemaakt en gevuld via stored proc (PK, VO-nummer, klant, datum, status)
- [ ] **CORE-02**: `core.dim_medewerker` aangemaakt en gevuld via stored proc (PK, naam, afdeling)
- [ ] **CORE-03**: `core.dim_artikel` aangemaakt en gevuld via stored proc (PK, code, omschrijving, artikelgroep)

### Core-laag — Feiten

- [ ] **CORE-04**: `core.fact_uren` aangemaakt en gevuld via stored proc — grain: één rij per urenregel (medewerker × productiebon × dag × VO), FK's naar alle dims
- [ ] **CORE-05**: Stored procs zijn idempotent (MERGE of TRUNCATE+INSERT patroon)

### Report-laag + Power BI

- [ ] **REPORT-01**: `report.v_uren_per_vo` view: totaal uren per VO, per medewerker, per periode
- [ ] **REPORT-02**: `report.v_nacalculatie_uren` view: uren per VO met datum, medewerker, productiebonnummer
- [ ] **REPORT-03**: Power BI Desktop .pbix rapport gebouwd voor pilot Horafrost: uren per VO, filter op periode en medewerker
- [ ] **REPORT-04**: Power BI connectie via Import mode (niet DirectQuery) — rapport refresht manueel via .pbix op laptop

## v2 Requirements — Fase 2: Inkoop-keten

### Exploratie (voorwaarde voor rest van Fase 2)

- [ ] **INKOOP-01**: SQL-exploratie uitgevoerd: FK-keten `inkoopfactuur → R_SALESORDER` bevestigd (tabelnames, kolomnamen, join-paden gedocumenteerd in `20-analyse/`)

### Raw uitbreiding

- [ ] **INKOOP-02**: `R_PURCHASEORDER`, `R_PURCHASEORDERLINE`, `R_PURCHASEINVOICE` (of equivalent) toegevoegd aan nachtelijke ETL en `raw.*`

### Core uitbreiding

- [ ] **INKOOP-03**: `core.dim_leverancier` aangemaakt en gevuld
- [ ] **INKOOP-04**: `core.fact_aankoop` aangemaakt en gevuld — grain: één rij per inkoopfactuur-regel, FK naar dim_verkooporder en dim_leverancier

### Report uitbreiding

- [ ] **INKOOP-05**: `report.v_nacalculatie_volledig` view: uren + aankoop gecombineerd per VO

## Uitgesteld

### Werkelijk vs. Begroot

- **BEGROTING-01**: Begrote uren/kosten per VO opzoeken in RidderIQ en vergelijken met werkelijk
- **BEGROTING-02**: Variantie-rapport (werkelijk − begroot) per VO in Power BI

*Reden uitstel: begroting-tabellen in RidderIQ nog onbevestigd; 3-6 maanden stabiele data nodig voor zinvolle vergelijking*

## Out of Scope

| Feature | Reden |
|---------|-------|
| Real-time data (DirectQuery) | VPN onbetrouwbaar, productie-DB ontzien |
| Power BI Service / cloud publish | Gateway vereist, M365-licentie onbekend — pilot eerst |
| Volledige DWH (SCDs, lineage) | Overkill voor dit schaal |
| SSIS / Azure Data Factory | Verkeerde toolset voor on-premises + kleine schaal |
| Forecasting / trend-analyse | Geen reporting-cultuur aanwezig — eerst fundament |
| Overhead-allocatie | Te complex voor v1, ETO-context maakt dit lastig |

## Traceability

| Requirement | Fase | Status |
|-------------|------|--------|
| INFRA-01 | Fase 1 (Phase 14) | Pending |
| INFRA-02 | Fase 1 (Phase 14) | Pending |
| INFRA-03 | Fase 1 (Phase 14) | Pending |
| INFRA-04 | Fase 1 (Phase 14) | Pending |
| ETL-01 | Fase 1 (Phase 15) | Pending |
| ETL-02 | Fase 1 (Phase 15) | Pending |
| ETL-03 | Fase 1 (Phase 15) | Pending |
| ETL-04 | Fase 1 (Phase 15) | Pending |
| ETL-05 | Fase 1 (Phase 15) | Pending |
| ETL-06 | Fase 1 (Phase 15) | Pending |
| ETL-07 | Fase 1 (Phase 15) | Pending |
| CORE-01 | Fase 1 (Phase 16) | Pending |
| CORE-02 | Fase 1 (Phase 16) | Pending |
| CORE-03 | Fase 1 (Phase 16) | Pending |
| CORE-04 | Fase 1 (Phase 16) | Pending |
| CORE-05 | Fase 1 (Phase 16) | Pending |
| REPORT-01 | Fase 1 (Phase 17) | Pending |
| REPORT-02 | Fase 1 (Phase 17) | Pending |
| REPORT-03 | Fase 1 (Phase 17) | Pending |
| REPORT-04 | Fase 1 (Phase 17) | Pending |
| INKOOP-01 | Fase 2 (Phase 18) | Pending |
| INKOOP-02 | Fase 2 (Phase 18) | Pending |
| INKOOP-03 | Fase 2 (Phase 18) | Pending |
| INKOOP-04 | Fase 2 (Phase 18) | Pending |
| INKOOP-05 | Fase 2 (Phase 18) | Pending |

**Coverage:**
- v1 requirements (Fase 1): 20 total
- v2 requirements (Fase 2): 5 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after initial definition v4.0*
