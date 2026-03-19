# Project Research Summary

**Project:** Spinnekop v4.0 — Rapporterings-DB + Nacalculatie (Nightly ETL + Power BI)
**Domain:** ERP reporting database — job costing / nacalculatie for ETO metal manufacturer
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH overall (stack HIGH, architecture HIGH, features MEDIUM, pitfalls MEDIUM-HIGH)

## Executive Summary

Spinnekop needs its first operational reporting capability: a nightly ETL pipeline that reads from the RidderIQ ERP (`Spinnekop Live 2`), writes to a separate `Spinnekop_Reporting` database on the same SQL Server 2016 instance, and surfaces data via Power BI Desktop. This is a well-understood pattern — the medallion architecture (raw/core/report schemas, star schema dimensional model, Python orchestration) is the industry standard for small on-premises BI setups and maps directly onto the existing infrastructure. No new tools, no cloud services, no license costs beyond what is already in place.

The recommended approach is a three-phase build: (1) ETL foundation with the uren-keten only (the one confirmed data chain), (2) pilot Power BI report for Horafrost as proof of concept for Francis and Carl, and (3) extension to the inkoop-keten and nacalculatie once the ETL is stable and the inkoop FK is confirmed. The uren-keten (`R_TIMESHEETLINE → R_PRODUCTIONORDER → R_SALESORDER`) is already confirmed working in the existing codebase. Everything else — inkoop-keten, begrote uren, verkoopprijs for margins — must be verified against live data before building. Build on what is confirmed; do not architect around assumptions.

The primary risks are operational, not architectural. VPN instability is a known reality on this project and will cause silent ETL failures without deliberate hardening. ERP schema drift from RidderIQ vendor updates has already happened once (server incident 2026-03-06). Power BI Service sharing requires an On-Premises Data Gateway that may not be licensed or hosted. All three risks are preventable in Phase 1 with standard patterns (control table, idempotent extracts, schema baseline). The architecture is sound; the work is disciplined execution.

---

## Key Findings

### Recommended Stack

The entire ETL can be built with tools already in use in this project. Python 3.11/3.12 orchestrates the pipeline; pyodbc 5.3.0 handles read/write against SQL Server 2016 via the already-installed ODBC Driver 17; pandas 2.x manages in-memory transforms for the small data volumes involved (thousands of rows, not millions); Windows Task Scheduler triggers the nightly job. Power BI Desktop (free) is sufficient for the pilot phase — no Pro license, no gateway, no new infrastructure.

The only meaningful decision pending is Power BI Service sharing: if Francis and Carl want web-accessible dashboards with automated refresh, a Pro license and an always-on gateway machine are required. This needs confirmation from Lebon IT before any commitment is made to management. For the pilot, sharing the `.pbix` file over Teams is the correct starting point.

**Core technologies:**
- Python 3.11/3.12: ETL orchestration — already in use, consistent toolchain, full git diff history
- pyodbc 5.3.0 + ODBC Driver 17: SQL Server connection — confirmed working against `10.0.1.5\RIDDERIQ`; do not upgrade to Driver 18 without TLS testing
- pandas 2.3.x: in-memory transformation — right-sized for ETO data volumes; avoid pandas 3.0 (breaking changes)
- SQLAlchemy 2.0.x: engine factory for `pandas.to_sql` with `fast_executemany=True` — 10-15x write speedup with minimal code
- Windows Task Scheduler: nightly job trigger — simpler than SQL Server Agent for a single Python script
- Power BI Desktop (free): report authoring and manual refresh — sufficient for pilot; Service requires license verification
- SQL Server 2016 Standard (existing): source + reporting DB host — same instance, no network hop, no new cost

**What not to use:** SSIS, dbt, Azure Data Factory, Airflow/Prefect, ODBC Driver 18 (untested), Power BI DirectQuery mode, pandas 3.0.

### Expected Features

The feature set has a clear two-tier split: the uren-keten is confirmed and can be built now; everything else requires data chain verification first. The MVP for the Horafrost pilot is intentionally narrow — uren per VO is the one number that answers "did this project cost what we expected in labour?"

**Must have (table stakes — Phase 1 and 1.x):**
- Uren per verkooporder (werkelijk) — the core nacalculatie metric; data chain confirmed
- ETL infrastructure (raw/core/report schemas) — prerequisite for everything else
- Power BI pilot rapport (Horafrost) — validates the concept for management
- Datum filtering (maand/kwartaal/jaar) — expected by any manager looking at operational data
- Overzicht alle VO's met status — "where do we stand?" is table stakes for an operational dashboard

**Should have (Phase 1.x — after pilot succeeds and data chains confirmed):**
- Aankoopkosten per VO (werkelijk) — blocked on inkoop FK verification
- Uren werkelijk vs. begroot — blocked on confirming where begrote uren live in RidderIQ
- Kosten per medewerker per periode — low complexity once uren-keten is live
- Nacalculatie view: uren + aankoop naast elkaar — the full picture

**Defer to v2+:**
- Marge per VO — requires verkoopprijs verification and stable base data
- Vergelijking soortgelijke projecten — requires 12+ months of data
- Doorlooptijd KPI — requires consistent date registration (verify first)
- Uren per productiestap — requires consistent bewerkingstype registration

**Do not build:** real-time dashboards, SCD Type 2 historisation, overhead-allocatie, forecasting, self-service BI, alerting, mobile dashboards.

### Architecture Approach

The three-layer medallion pattern (raw / core / report) on a single SQL Server database is the right architecture. Raw schema holds append-only daily snapshots tagged with `snapshot_date` — this is the disaster recovery layer and the replayability mechanism. Core schema holds a classic star schema (dim_datum, dim_vo, dim_medewerker, dim_artikel, fact_uren) populated via T-SQL MERGE stored procedures called from Python. Report schema holds pure SQL views — no logic, only joins and column aliases — which Power BI reads via Import mode.

The critical architectural rule: Python handles transport (source to raw), SQL handles transformation (raw to core), and the boundary between them is the raw schema. Never mix. Business logic that crosses this boundary becomes impossible to debug.

**Major components:**
1. `raw` schema — daily snapshots with `snapshot_date`; append-only for transactional tables, full-replace for reference tables; absorbs ERP schema changes without touching core
2. `core` schema — star schema with surrogate keys; dims loaded via MERGE (SCD Type 1); fact_uren as the transaction fact table with grain = one timesheetline per employee per production order per day
3. `report` schema — pure SQL views; stable names; Power BI connects here only
4. `etl_nightly.py` — orchestrator: connect, extract (extract.py), transform (transform.py via EXEC sp_load_*), log (etl_log.py)
5. `raw.etl_run_log` — control table with run metadata; the single most important operational addition
6. `dim_datum` — pre-populated calendar table 2018-2035; never touched by nightly ETL

Build order is strict: database → schemas → raw tables → dim_datum → other dims → fact_uren → stored procedures → report views → first ETL run. fact_aankoop is explicitly Phase 2.

### Critical Pitfalls

1. **Silent ETL failure** — Task Scheduler shows green even when the Python script exits with an exception. Prevention: write to `raw.etl_run_log` on every run; add a Power BI "data freshness" card showing `MAX(snapshot_date)` on every report page. Build this in Phase 1, before the first demo.

2. **VPN drop mid-run leaving partial raw data** — pyodbc's default connection timeout is unlimited; VPN drops are a documented reality on this project. Prevention: `pyodbc.pooling = False` at script start; `Connection Timeout=15` in connection string; DELETE the current day's raw rows at the start of each table extract (idempotency). This must be baked in from the first table — retrofitting is painful.

3. **ERP schema drift from RidderIQ vendor updates** — Ridder Support updates have already caused a server restore on this project. Prevention: always SELECT named columns (never `SELECT *`); maintain `ridderiq-schema-baseline.sql` in git; run schema snapshot comparison nightly via `INFORMATION_SCHEMA.COLUMNS`. After any RidderIQ update, run schema comparison before resuming ETL.

4. **Power BI Service gateway requirement** — a `.pbix` that works on a VPN-connected laptop will fail to auto-refresh in Power BI Service without an always-on On-Premises Data Gateway. Prevention: confirm M365 plan with Lebon IT before promising scheduled refresh; start with Power BI Desktop + manual refresh for the pilot.

5. **Production ERP locking** — full-table SELECT scans on `Spinnekop Live 2` during business hours can block RidderIQ users. Prevention: schedule ETL at 02:00; add `WITH (NOLOCK)` to all source queries from day one.

---

## Implications for Roadmap

Research points clearly to a three-phase structure driven by data chain confirmation gates. Phase 2 cannot start before the inkoop FK is confirmed; Phase 3 cannot start before Phase 2 data is stable and begrote uren are verified. Do not skip the gates.

### Phase 1: ETL Foundation + Uren Pilot (Horafrost)

**Rationale:** The uren-keten is the only confirmed data chain. This is the only thing that can be built without VPN investigation first. Everything else depends on the infrastructure created here. The control table and idempotency patterns must exist before the pipeline is shown to stakeholders.

**Delivers:** Working nightly ETL for uren-keten; `Spinnekop_Reporting` database with raw/core/report schemas; `fact_uren` populated; Power BI pilot report for Horafrost showing uren per VO with datum filter; freshness card; run log.

**Features addressed:** Uren per VO (werkelijk), datum filtering, Power BI pilot rapport, ETL infrastructure.

**Pitfalls to prevent in this phase:** All five critical pitfalls — control table (P1), idempotent VPN-safe extracts (P2), schema baseline (P3), Import mode not DirectQuery (P4), WITH NOLOCK + 02:00 schedule (P5).

**Research flag:** Standard patterns — no phase research needed. The uren-keten, pyodbc stack, and three-layer architecture are all confirmed and well-documented.

### Phase 2: Inkoop-Keten + Volledige Nacalculatie

**Rationale:** Blocked on finding the FK between inkoopfacturen and verkooporders in RidderIQ. This FK must be confirmed in a VPN SQL-exploration session before any build starts. Once confirmed, `fact_aankoop` extends the existing star schema and the report layer gets the nacalculatie view (uren + aankoop naast elkaar).

**Delivers:** `fact_aankoop` in core schema; ETL extended with inkoopfacturen snapshot; nacalculatie view combining uren and aankoopkosten per VO; overzicht alle VO's met status.

**Features addressed:** Aankoopkosten per VO (werkelijk), nacalculatie view, overzicht VO's, kosten per medewerker.

**Pitfalls to prevent:** Schema baseline extended for inkoop tables; same idempotency pattern applied to new raw tables.

**Research flag:** Needs SQL exploration (not phase research) — the inkoop FK must be found before building. This is a data discovery task, not an architecture question.

### Phase 3: Vergelijking + Begroting (Werkelijk vs. Begroot)

**Rationale:** Requires (a) begrote uren located and verified in RidderIQ offerte/calculatie tables, and (b) verkoopprijs confirmed as reliable for marge calculation. Both are unknowns. This phase also requires 3-6 months of Phase 1-2 data before trendanalyse is meaningful.

**Delivers:** Werkelijk vs. begroot rapport; marge per VO (if verkoopprijs confirmed); doorlooptijd KPI (if datum registration proven consistent); wekelijkse uren-trend per vestiging.

**Features addressed:** Uren werkelijk vs. begroot, marge per VO, doorlooptijd KPI.

**Research flag:** Needs SQL exploration to locate begroting tables in RidderIQ before phase planning. The offerte/calculatie data chain is unconfirmed. Flag for research-phase during roadmap planning.

### Phase Ordering Rationale

- Phase 1 is independent of all data chain unknowns — it can start immediately.
- Phases 2 and 3 are both gated behind SQL exploration sessions. These explorations should happen during Phase 1 build so Phase 2 can start without delay.
- The feature dependency graph from FEATURES.md is explicit: marge requires both uren and aankoop; "vs. begroot" requires begroting data; neither makes sense before the basic "werkelijk" numbers are stable and trusted.
- Architecture build order dictates Phase 1 scope: dims before facts, fact_uren before fact_aankoop, raw layer before core layer before report layer.

### Research Flags

**Needs SQL exploration before planning (not full research-phase):**
- Phase 2: locate `FK inkoopfactuur → verkooporder` in `Spinnekop Live 2` — run during Phase 1 build
- Phase 3: locate begroting/calculatie tables and verkoopprijs field in RidderIQ — run during Phase 2

**Standard patterns (no research needed):**
- Phase 1: three-layer architecture, pyodbc ETL, Task Scheduler, Power BI Import mode are all well-documented and confirmed for this stack

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All core technologies confirmed working against this exact SQL Server instance; pattern matches existing codebase conventions |
| Architecture | HIGH | Three-layer medallion + star schema is well-established; SQL Server 2016 Standard constraints verified; all required features confirmed available in Standard edition |
| Features | MEDIUM | Uren-keten confirmed (HIGH); inkoop-keten TBD (LOW); begroting data TBD (LOW); ETO nacalculatie theory well-established (HIGH) |
| Pitfalls | MEDIUM-HIGH | ETL and data warehouse pitfalls well-documented across multiple sources; VPN-specific behaviour verified against pyodbc issue tracker; Power BI gateway requirement confirmed in official Microsoft docs |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Inkoop FK** (`inkoopfactuur → verkooporder`): must be confirmed in SQL exploration before Phase 2 design. Run `SELECT TOP 5 * FROM [inkoopfactuur table]` and trace FK chain during first available VPN session. This is the single highest-priority unknown.
- **Begrote uren location**: offerte/calculatie module in RidderIQ must be queried to find where begrote uren are stored and whether they are reliable enough for "werkelijk vs. begroot" comparison. Block Phase 3 planning until confirmed.
- **Verkoopprijs reliability**: `R_SALESORDER` likely contains a price field but its completeness and reliability for all orders is unverified. Required for marge calculation in Phase 3.
- **Power BI Service licensing**: confirm with Lebon IT whether the current M365 plan includes Power BI Pro. This determines whether the pilot can be shared as a web URL or must remain a `.pbix` file sent over Teams.
- **SQL Server 2016 end of extended support** (July 2026): extended security support ends mid-2026. The reporting DB workload is read-only against production so the risk is contained, but this should be flagged in the roadmap as a future migration item.

---

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — confirmed data chains, pilot scope, architecture decisions, VPN constraints
- pyodbc 5.3.0 PyPI — version and Windows wheel confirmation
- Microsoft Learn: DirectQuery vs Import mode in Power BI — import mode recommendation
- Microsoft Learn: Data refresh in Power BI — gateway requirement for Service
- Microsoft Learn: SQL Server transaction locking guide — NOLOCK rationale
- SQLAlchemy 2.0 MSSQL dialect docs — `fast_executemany` connection pattern
- Microsoft Fabric dimensional modeling guides — star schema patterns

### Secondary (MEDIUM confidence)
- Brent Ozar: SQL Server 2016 Standard Edition features — Standard edition feature confirmation
- pyodbc GitHub issue #734 — connection pool behaviour after VPN drop
- MSSQLTips: date dimension creation — dim_datum design
- Kimball Group Design Tip #107 — MERGE for slowly changing dimensions
- DSW: Overcome Cost Issues in ETO Manufacturing — ETO nacalculatie theory
- NetSuite: Job Costing Defined — job costing fundamentals

### Tertiary (LOW confidence)
- Airbyte: ETL pipeline pitfalls — general ETL pitfall patterns
- Red Gate Simple Talk: How to get ETL horribly wrong — practitioner post-mortem
- Genius ERP: How ERPs help ETO manufacturers — ETO ERP requirements
- Integrate.io: Schema drift in ETL pipelines — schema drift patterns

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
