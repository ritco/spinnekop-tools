# Architecture Research

**Domain:** Three-layer reporting database on SQL Server 2016 — ERP-based nacalculatie
**Researched:** 2026-03-19
**Confidence:** HIGH (three-layer pattern is well-established; SQL Server 2016 Standard constraints verified)

## Standard Architecture

### System Overview

```
+--------------------------------------------------+
|  SOURCE: Spinnekop Live 2 (RidderIQ ERP)         |
|  10.0.1.5\RIDDERIQ — SQL Server 2016             |
|  R_TIMESHEETLINE, R_PRODUCTIONORDER,             |
|  R_SALESORDER, R_ITEM, R_EMPLOYEE, ...           |
+---------------------+----------------------------+
                      | nightly Python ETL
                      | (Windows Task Scheduler)
                      v
+--------------------------------------------------+
|  DATABASE: Spinnekop_Reporting                   |
+--------------------------------------------------+
|                                                  |
|  SCHEMA: raw  (Bronze / Landing Zone)            |
|  +-----------+  +-----------+  +----------+      |
|  | R_TIMESHEET|  |R_PROD_ORDER|  |R_SALESORD|    |
|  | LINE_snap  |  |_snap       |  |ER_snap   |    |
|  +-----------+  +-----------+  +----------+      |
|  append-only, snapshot_date column, no FK        |
|                                                  |
+--------------------------------------------------+
                      |
                      | SQL stored procedures
                      | (upsert via MERGE)
                      v
+--------------------------------------------------+
|  SCHEMA: core  (Silver / Star Schema)            |
|  +----------+  +----------+  +---------+         |
|  | dim_datum |  | dim_vo   |  |dim_mede-|         |
|  |           |  |          |  |werker   |         |
|  +----------+  +----------+  +---------+         |
|  +----------+                                     |
|  | dim_artikel|                                   |
|  +----------+                                     |
|  +------------------------------------------+    |
|  | fact_uren                                 |    |
|  +------------------------------------------+    |
|  +------------------------------------------+    |
|  | fact_aankoop  (later milestone)           |    |
|  +------------------------------------------+    |
|                                                  |
+--------------------------------------------------+
                      |
                      | SQL views (no logic)
                      v
+--------------------------------------------------+
|  SCHEMA: report  (Gold / Power BI interface)     |
|  +------------------+  +---------------------+   |
|  | nacalculatie_uren |  | kpi_vo_doorlooptijd |   |
|  +------------------+  +---------------------+   |
|  +------------------+                            |
|  | open_vo_overzicht|                            |
|  +------------------+                            |
+--------------------------------------------------+
                      |
                      | DirectQuery or Import
                      v
+--------------------------------------------------+
|  Power BI Desktop / Pro                          |
+--------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| raw schema | Exact copy of source rows + snapshot_date. No transformations. Absorbs schema changes from RidderIQ. | Python TRUNCATE+INSERT or append per table type |
| core schema | Business logic, surrogate keys, conformed dimensions, star schema. Single source of truth. | SQL stored procedures called from Python |
| report schema | Presentation-layer views optimized for Power BI. No logic, only joins and column aliases. | SQL views, created once, maintained as requirements grow |
| ETL Python script | Orchestrates: connect source, populate raw, call core procs, log results | Single `etl_nightly.py` via Task Scheduler |
| dim_datum | Calendar table — pre-populated, never updated by ETL | One-time SQL script, covers 2020-2035 |

---

## Recommended Project Structure

```
scripts/
└── etl/
    ├── etl_nightly.py          # Main orchestrator script
    ├── etl_config.py           # Connection strings, schema names, table list
    ├── extract.py              # Source -> raw layer (pyodbc reads + bulk insert)
    ├── transform.py            # Calls SQL stored procedures for raw -> core
    ├── etl_log.py              # Write run log to raw.etl_run_log
    └── sql/
        ├── 00_create_database.sql    # One-time: CREATE DATABASE + schemas
        ├── 01_create_raw.sql         # One-time: raw table DDL
        ├── 02_create_dim_datum.sql   # One-time: calendar table + populate
        ├── 03_create_core.sql        # One-time: dim + fact table DDL
        ├── 04_create_report.sql      # One-time: report views DDL
        ├── sp_load_dim_vo.sql        # Stored proc: upsert dim_vo
        ├── sp_load_dim_medewerker.sql
        ├── sp_load_dim_artikel.sql
        ├── sp_load_fact_uren.sql     # Stored proc: load fact_uren from raw
        └── sp_load_fact_aankoop.sql  # Stored proc: load fact_aankoop (later)
```

### Structure Rationale

- **etl/sql/**: All DDL and stored procedures live as `.sql` files under version control. Python only calls `EXEC sp_load_*` — business logic stays in SQL where it belongs.
- **extract.py separated from transform.py**: Source read errors are isolated from transformation errors. Easy to re-run just the extract or just the transform step.
- **etl_config.py as single config point**: Connection strings, table names, schema names — one place to change when promoting to production or adding new source tables.

---

## Architectural Patterns

### Pattern 1: Raw Layer — Daily Snapshot Append

**What:** Each night, Python copies the full contents of relevant RidderIQ tables into raw, tagged with today's `snapshot_date`. Existing rows are never deleted or updated.

**When to use:** For slowly changing operational tables like R_SALESORDER (verkooporder status changes over time). Append-only means you can reconstruct the state of a VO on any past date.

**Trade-offs:** Storage grows over time (~1-2 years of RidderIQ data = tens of MB at most for this scale). Queries against raw must always filter on `snapshot_date = MAX(snapshot_date)` or a specific date to get current state. This is a worthwhile trade for auditability.

**Exception — full replace tables:** For reference tables that are small and stable (R_ITEM, R_EMPLOYEE), TRUNCATE + INSERT on every run is simpler and sufficient. No snapshot_date needed; raw just holds the current state.

**Implementation:**
```python
# extract.py — append pattern for R_TIMESHEETLINE
def extract_append(src_conn, dst_conn, table: str, snapshot_date: str):
    cursor_src = src_conn.cursor()
    cursor_src.execute(f"SELECT * FROM {table}")
    rows = cursor_src.fetchall()
    cols = [d[0] for d in cursor_src.description]

    cursor_dst = dst_conn.cursor()
    cursor_dst.fast_executemany = True
    placeholders = ', '.join(['?'] * (len(cols) + 1))
    col_list = ', '.join(cols) + ', snapshot_date'
    cursor_dst.executemany(
        f"INSERT INTO raw.{table}_snap ({col_list}) VALUES ({placeholders})",
        [(*row, snapshot_date) for row in rows]
    )
    dst_conn.commit()
```

### Pattern 2: Core Layer — MERGE-based Upsert via Stored Procedures

**What:** Python calls stored procedures that read from raw (latest snapshot) and upsert into core dimension and fact tables using T-SQL MERGE. All business logic lives in SQL.

**When to use:** Always for the core layer. Python should not contain transformation logic — SQL MERGE is the right tool because it runs set-based and handles INSERT/UPDATE/DELETE atomically.

**Trade-offs:** Stored procedures are harder to unit test than Python, but for a stable ERP source this is a non-issue. The benefit is that performance is 10-100x better than row-by-row Python for large tables.

**SCD strategy:** Use SCD Type 1 (overwrite) for all dimensions initially. Verkooporder name, employee name, article description changes are rare and current values are sufficient for nacalculatie. Introduce SCD Type 2 only if historical analysis of dimension changes becomes a specific requirement.

**Implementation:**
```sql
-- sp_load_dim_vo.sql
CREATE OR ALTER PROCEDURE core.sp_load_dim_vo AS
BEGIN
    SET NOCOUNT ON;

    -- Source: latest snapshot from raw
    WITH latest AS (
        SELECT *
        FROM raw.R_SALESORDER_snap
        WHERE snapshot_date = (SELECT MAX(snapshot_date)
                               FROM raw.R_SALESORDER_snap)
    )
    MERGE core.dim_vo AS target
    USING latest AS source
        ON target.vo_nummer = source.CODE

    WHEN MATCHED THEN UPDATE SET
        target.omschrijving  = source.DESCRIPTION,
        target.klant         = source.CUSTOMERNAME,
        target.status        = source.STATUSDESCRIPTION,
        target.datum_aanmaak = source.CREATIONDATE,
        target.gewijzigd_op  = GETDATE()

    WHEN NOT MATCHED BY TARGET THEN INSERT
        (vo_nummer, omschrijving, klant, status, datum_aanmaak, aangemaakt_op)
    VALUES
        (source.CODE, source.DESCRIPTION, source.CUSTOMERNAME,
         source.STATUSDESCRIPTION, source.CREATIONDATE, GETDATE());
END
```

### Pattern 3: Report Layer — Pure Views, Zero Logic

**What:** The report schema contains only views. Each view is a join across core tables, with business-readable column aliases. No aggregations, no CASE logic, no subqueries with business meaning.

**When to use:** Always. Views are the Power BI interface. They must be stable in name and structure. If Power BI needs a different calculation, add a new measure in DAX — do not change the view.

**Trade-offs:** Regular views re-execute the underlying query on every Power BI refresh. For the scale of this project (hundreds of thousands of rows max), this is fine with proper indexes on core tables. Indexed views are not needed and add maintenance overhead.

**Implementation:**
```sql
-- 04_create_report.sql
CREATE OR ALTER VIEW report.nacalculatie_uren AS
SELECT
    f.fact_uren_id,
    d.datum,
    d.jaar,
    d.kwartaal,
    d.maand_naam,
    d.week_nummer,
    v.vo_nummer,
    v.omschrijving        AS vo_omschrijving,
    v.klant,
    m.medewerker_naam,
    m.afdeling,
    a.artikel_code,
    a.artikel_omschrijving,
    f.geboekte_uren,
    f.geplande_uren,
    f.afwijking_uren
FROM core.fact_uren f
JOIN core.dim_datum    d ON f.datum_sk     = d.datum_sk
JOIN core.dim_vo       v ON f.vo_sk        = v.vo_sk
JOIN core.dim_medewerker m ON f.medewerker_sk = m.medewerker_sk
JOIN core.dim_artikel  a ON f.artikel_sk   = a.artikel_sk;
```

---

## Data Flow

### Nightly ETL Flow

```
22:00 Task Scheduler triggers etl_nightly.py
    |
    +-- 1. Connect to Spinnekop Live 2 (pyodbc, VPN must be up)
    +-- 2. Connect to Spinnekop_Reporting (same instance)
    |
    +-- 3. EXTRACT phase (extract.py)
    |       Full replace tables: R_ITEM, R_EMPLOYEE, R_ITEMGROUP
    |         TRUNCATE raw.R_ITEM_snap → INSERT all rows
    |       Append tables: R_TIMESHEETLINE, R_PRODUCTIONORDER, R_SALESORDER
    |         INSERT all rows WHERE source_id NOT IN raw (incremental)
    |         OR full append if simpler (small tables, <100K rows)
    |
    +-- 4. TRANSFORM phase (transform.py)
    |       EXEC core.sp_load_dim_vo
    |       EXEC core.sp_load_dim_medewerker
    |       EXEC core.sp_load_dim_artikel
    |       EXEC core.sp_load_fact_uren
    |
    +-- 5. LOG phase (etl_log.py)
    |       INSERT raw.etl_run_log (run_date, duration_sec, rows_extracted,
    |                               rows_loaded, status, error_message)
    |
    +-- 6. Done — report layer views are live immediately
```

### Key Data Chain: Uren

```
R_TIMESHEETLINE (raw)
    FK_PRODUCTIONORDER --> R_PRODUCTIONORDER (raw)
                              FK_SALESORDER --> R_SALESORDER (raw)
                              FK_ITEM        --> R_ITEM (raw)
    FK_EMPLOYEE        --> R_EMPLOYEE (raw)
    WORKEDTIME / PLANNEDTIME --> geboekte/geplande uren
```

This chain is already confirmed working in the existing codebase (see `sql_validator.py` and project memory).

---

## Table Designs

### dim_datum (Calendar Table)

Pre-populated once for 2018-2035. Never touched by the nightly ETL.

```sql
CREATE TABLE core.dim_datum (
    datum_sk        INT          NOT NULL PRIMARY KEY,  -- YYYYMMDD as INT
    datum           DATE         NOT NULL UNIQUE,
    jaar            SMALLINT     NOT NULL,
    kwartaal        TINYINT      NOT NULL,              -- 1-4
    maand           TINYINT      NOT NULL,              -- 1-12
    maand_naam      NVARCHAR(20) NOT NULL,              -- 'januari', etc.
    week_nummer     TINYINT      NOT NULL,              -- ISO week
    dag_in_week     TINYINT      NOT NULL,              -- 1=Mon, 7=Sun
    dag_naam        NVARCHAR(20) NOT NULL,
    is_werkdag      BIT          NOT NULL DEFAULT 1,
    jaar_maand      CHAR(7)      NOT NULL,              -- '2026-03'
    jaar_kwartaal   CHAR(7)      NOT NULL               -- '2026-Q1'
);
-- surrogate key strategy: datum_sk = CAST(FORMAT(datum, 'yyyyMMdd') AS INT)
-- e.g. 2026-03-19 → 20260319
-- This makes it human-readable and eliminates IDENTITY, no MERGE needed
```

**Rationale for INT surrogate key on datum:** A date dimension is the one case where a natural key (the date itself formatted as YYYYMMDD integer) outperforms a system-generated IDENTITY. It stays human-readable in the fact table without joins for debugging.

### dim_vo (Verkooporder)

```sql
CREATE TABLE core.dim_vo (
    vo_sk           INT IDENTITY(1,1) PRIMARY KEY,
    vo_nummer       NVARCHAR(50) NOT NULL UNIQUE,  -- natural key from RidderIQ CODE
    omschrijving    NVARCHAR(200),
    klant           NVARCHAR(200),
    status          NVARCHAR(50),
    datum_aanmaak   DATE,
    aangemaakt_op   DATETIME2    NOT NULL DEFAULT GETDATE(),
    gewijzigd_op    DATETIME2    NOT NULL DEFAULT GETDATE()
);
```

### dim_medewerker

```sql
CREATE TABLE core.dim_medewerker (
    medewerker_sk   INT IDENTITY(1,1) PRIMARY KEY,
    medewerker_id   INT          NOT NULL UNIQUE,  -- natural key: PK_R_EMPLOYEE
    medewerker_naam NVARCHAR(200) NOT NULL,
    login_naam      NVARCHAR(100),
    afdeling        NVARCHAR(100),
    actief          BIT          NOT NULL DEFAULT 1,
    aangemaakt_op   DATETIME2    NOT NULL DEFAULT GETDATE(),
    gewijzigd_op    DATETIME2    NOT NULL DEFAULT GETDATE()
);
```

### dim_artikel

```sql
CREATE TABLE core.dim_artikel (
    artikel_sk      INT IDENTITY(1,1) PRIMARY KEY,
    artikel_code    NVARCHAR(50) NOT NULL UNIQUE,  -- natural key: CODE from R_ITEM
    artikel_omschrijving NVARCHAR(500),
    artikelgroep    NVARCHAR(100),
    eenheid         NVARCHAR(20),
    aangemaakt_op   DATETIME2    NOT NULL DEFAULT GETDATE(),
    gewijzigd_op    DATETIME2    NOT NULL DEFAULT GETDATE()
);
```

### fact_uren (Transaction Fact Table)

```sql
CREATE TABLE core.fact_uren (
    fact_uren_id        INT IDENTITY(1,1) PRIMARY KEY,
    -- dimension keys (surrogate)
    datum_sk            INT  NOT NULL REFERENCES core.dim_datum(datum_sk),
    vo_sk               INT  NOT NULL REFERENCES core.dim_vo(vo_sk),
    medewerker_sk       INT  NOT NULL REFERENCES core.dim_medewerker(medewerker_sk),
    artikel_sk          INT  NOT NULL REFERENCES core.dim_artikel(artikel_sk),
    -- natural keys (for traceability back to source)
    source_timesheetline_pk  INT NOT NULL,
    source_productionorder_pk INT NOT NULL,
    -- measures
    geboekte_uren       DECIMAL(10,2),
    geplande_uren       DECIMAL(10,2),
    afwijking_uren      AS (geboekte_uren - geplande_uren) PERSISTED,
    -- metadata
    snapshot_date       DATE NOT NULL,  -- which raw snapshot this came from
    geladen_op          DATETIME2 NOT NULL DEFAULT GETDATE()
);
CREATE INDEX ix_fact_uren_vo      ON core.fact_uren(vo_sk);
CREATE INDEX ix_fact_uren_datum   ON core.fact_uren(datum_sk);
CREATE INDEX ix_fact_uren_medew   ON core.fact_uren(medewerker_sk);
```

**Grain:** One row per timesheetline entry (one employee, one production order, one day).

### raw.etl_run_log

```sql
CREATE TABLE raw.etl_run_log (
    run_id          INT IDENTITY(1,1) PRIMARY KEY,
    run_date        DATETIME2    NOT NULL DEFAULT GETDATE(),
    stap            NVARCHAR(50) NOT NULL,  -- 'extract', 'transform', 'done'
    tabel           NVARCHAR(100),
    rijen_bron      INT,
    rijen_geladen   INT,
    duur_seconden   DECIMAL(8,2),
    status          NVARCHAR(20) NOT NULL,  -- 'ok', 'error'
    foutmelding     NVARCHAR(2000)
);
```

---

## Build Order

Build order is dictated by foreign key dependencies. Each step can only proceed if the previous step exists.

| Step | Action | Dependency |
|------|--------|------------|
| 1 | CREATE DATABASE Spinnekop_Reporting | None — run once on server |
| 2 | CREATE SCHEMA raw, core, report | Database exists |
| 3 | CREATE raw tables (all _snap tables + etl_run_log) | Schemas exist |
| 4 | CREATE core.dim_datum + populate | raw schema exists |
| 5 | CREATE core.dim_vo, dim_medewerker, dim_artikel | dim_datum exists |
| 6 | CREATE core.fact_uren | All four dims exist (FK references) |
| 7 | CREATE stored procedures sp_load_dim_* | raw + core tables exist |
| 8 | CREATE stored procedure sp_load_fact_uren | All dims loaded (first ETL run needed) |
| 9 | CREATE report views | core tables + procs exist |
| 10 | First ETL run (test, then schedule) | Everything above complete |
| 11 | fact_aankoop (next milestone) | FK-verkenning inkoopfacturen done |

**First milestone scope:** Steps 1-10, uren only. fact_aankoop is explicitly Phase 2.

---

## Incremental vs Full-Refresh Strategy

| Table | Strategy | Rationale |
|-------|----------|-----------|
| raw.R_TIMESHEETLINE_snap | Append: INSERT WHERE PK NOT IN raw | Timesheet records accumulate; never deleted |
| raw.R_PRODUCTIONORDER_snap | Append with snapshot_date | Status changes over time, want history |
| raw.R_SALESORDER_snap | Append with snapshot_date | VO status changes, want history |
| raw.R_ITEM_snap | Full replace (TRUNCATE + INSERT) | Reference data, small, no history needed |
| raw.R_EMPLOYEE_snap | Full replace (TRUNCATE + INSERT) | Small, no history needed |
| core.dim_* | MERGE upsert (SCD Type 1) | Current state sufficient, overwrite on change |
| core.fact_uren | Incremental: only rows not yet loaded | Immutable facts; use source_timesheetline_pk as dedup key |
| report.* | Views — no data stored | Always current; no refresh needed |

**Dedup key for fact_uren:** Use `source_timesheetline_pk` as the natural key to prevent duplicate rows on re-runs. Add UNIQUE constraint or check in the stored proc.

---

## SQL Server 2016 Standard Edition Constraints

| Feature | Standard Behaviour | Impact |
|---------|-------------------|--------|
| Indexed views | Allowed, but query optimizer will NOT auto-match without NOEXPAND hint | Avoid indexed views in report schema — regular views are sufficient. If needed, add WITH (NOEXPAND) in Power BI DirectQuery views. |
| Partitioning | Table/index partitioning available in Standard since 2016 SP1 | Not needed at this scale; skip |
| In-Memory OLTP | Not available in Standard | Not needed |
| Always On | Basic availability groups only | Not relevant for this single-instance setup |
| Compression | Row/page compression available | Consider on raw tables after 1 year of data |
| Max RAM | 128 GB in Standard | No issue |
| Computed columns PERSISTED | Fully supported | Used in fact_uren.afwijking_uren |
| MERGE statement | Fully supported | Used in all sp_load_dim_* |
| Schemas | Fully supported | Core pattern for the three-layer design |

**Verdict:** All required features are available in SQL Server 2016 Standard. No Enterprise-only features are needed or used.

---

## Anti-Patterns

### Anti-Pattern 1: Business Logic in report Views

**What people do:** Put CASE WHEN statements, complex aggregations, business rule calculations directly in report schema views.

**Why it's wrong:** When a business rule changes, you must find and update every view that contains it. Power BI caches the view structure. Report views become the hardest layer to maintain.

**Do this instead:** Put business logic in core stored procedures or computed columns on fact/dim tables. Report views should be dumb joins and column renames only.

### Anti-Pattern 2: Row-by-Row Python Inserts into raw

**What people do:** Loop through source rows in Python and execute one INSERT per row.

**Why it's wrong:** At 50,000 timesheetlines, row-by-row insertion takes minutes instead of seconds. Network round-trips dominate.

**Do this instead:** Use `cursor.fast_executemany = True` with `cursor.executemany()`. Benchmarks show 100x speedup. For very large tables (>500K rows), consider BCP or BULK INSERT via a temp file.

### Anti-Pattern 3: Transformation Logic Split Between Python and SQL

**What people do:** Do some transformations in Python (mapping, filtering) and some in SQL stored procedures.

**Why it's wrong:** When debugging a wrong number in a report, you must trace through two languages and two execution environments to find the error.

**Do this instead:** Python handles transport (read source, write to raw, call procs). SQL handles transformation (raw to core). The boundary is the raw schema. Never mix.

### Anti-Pattern 4: Loading fact_uren Before Dimensions Are Populated

**What people do:** Run fact load and dimension load in parallel or wrong order.

**Why it's wrong:** FK constraints on fact_uren reference dim tables. If a VO or employee is missing from a dim, the fact row either fails with FK violation or gets an unresolvable NULL foreign key.

**Do this instead:** Enforce load order in etl_nightly.py: dims always before facts. Log a warning (not a crash) if a source key is not found in a dim — this reveals data quality issues in the source.

### Anti-Pattern 5: No ETL Run Log

**What people do:** Run the ETL silently; check Power BI next morning to see if it worked.

**Why it's wrong:** When an ETL fails at 03:00, nobody knows until a user reports stale data. Root cause is hard to trace.

**Do this instead:** Write raw.etl_run_log at the start and end of every ETL run, per table. Email or log alert on error status. This costs 10 lines of Python and is the single most valuable operational addition.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Spinnekop Live 2 (source) | pyodbc read-only connection, SQL Server 2016 | Use dedicated read-only SQL login; never write to Live 2 from ETL |
| Spinnekop_Reporting (target) | pyodbc read-write, same instance | Separate database isolates ETL activity from ERP transactions |
| Windows Task Scheduler | Triggers etl_nightly.py at fixed time (22:00) | Run as service account; log stdout/stderr to file |
| Power BI Desktop | DirectQuery or Import against report schema views | Import mode is faster for small datasets; DirectQuery for always-current data |
| VPN (OpenVPN) | Must be up for ETL to reach 10.0.1.5 | ETL must handle connection failure gracefully: log error, do not crash silently |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Python (extract) → raw schema | pyodbc bulk INSERT, fast_executemany | Python owns this boundary; SQL Server has no pull capability from ETL side |
| raw schema → core schema | T-SQL MERGE inside stored procedures | SQL owns this boundary; Python only calls EXEC |
| core schema → report schema | SQL views — no data movement | Views are pointers, not copies; instant consistency |
| report schema → Power BI | ODBC/native connector | DirectQuery uses report.* views by name; keep view names stable |

---

## Sources

- [SQL Server Data Warehouse Architecture Guide — WhereScape](https://www.wherescape.com/blog/sql-server-data-warehouse-architecture-guide/)
- [Dimensional Modeling: Fact Tables — Microsoft Learn (Fabric)](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables)
- [Dimensional Modeling: Dimension Tables — Microsoft Learn (Fabric)](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables)
- [Creating a Date Dimension in SQL Server — MSSQLTips](https://www.mssqltips.com/sqlservertip/4054/creating-a-date-dimension-or-calendar-table-in-sql-server/)
- [Design Guidance for Date Tables in Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables)
- [Indexed Views in SQL Server Standard Edition — Greg Low](https://blog.greglow.com/2019/04/19/sql-do-indexed-views-really-require-enterprise-edition-of-sql-server/)
- [SQL MERGE for Slowly Changing Dimensions — Kimball Group Design Tip #107](https://www.kimballgroup.com/2008/11/design-tip-107-using-the-sql-merge-statement-for-slowly-changing-dimension-processing/)
- [Pyodbc fast_executemany — 100x faster inserts (Medium/TDS Archive)](https://medium.com/data-science/how-i-made-inserts-into-sql-server-100x-faster-with-pyodbc-5a0b5afdba5)
- [Why Surrogate Keys are Needed for SQL Server Data Warehouse — MSSQLTips](https://www.mssqltips.com/sqlservertip/5602/why-surrogate-keys-are-needed-for-a-sql-server-data-warehouse/)
- [Medallion Architecture — Databricks](https://www.databricks.com/blog/what-is-medallion-architecture)

---
*Architecture research for: Three-layer reporting database (raw/core/report) on SQL Server 2016 Standard for ERP-based nacalculatie*
*Researched: 2026-03-19*
