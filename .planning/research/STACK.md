# Stack Research

**Domain:** Nightly ETL pipeline — SQL Server to SQL Server reporting database with Power BI
**Researched:** 2026-03-19
**Confidence:** HIGH (core decisions), MEDIUM (Power BI refresh path pending M365 license check)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 or 3.12 | ETL orchestration | Already in use in this project; scripts are consistent with existing toolchain; no new runtime to maintain |
| pyodbc | 5.3.0 | Read from `Spinnekop Live 2`, write to `Spinnekop_Reporting` | Direct ODBC driver access, already proven working against this exact SQL Server instance; `fast_executemany=True` gives bulk-load speed without extra tooling |
| pandas | 2.x (2.3.x) | In-memory data transformation | Right-sized for ETO data volumes (thousands of rows, not millions); `read_sql` + DataFrame transforms keep ETL logic readable; avoid pandas 3.0 for now (breaking changes in 2.x → 3.0 migration path) |
| SQL Server 2016 Standard | 13.x (existing) | Source DB + reporting DB host | Single instance, same server — no network hop, no licensing cost, no new infrastructure |
| Windows Task Scheduler | built-in | Nightly job scheduling | SQL Server Agent is available on Standard edition but adds unnecessary complexity for a single Python script; Task Scheduler is simpler, already used for other ops tasks, zero extra config |
| Power BI Desktop | free | Report authoring + refresh | Free tier is sufficient for one-person authoring; no Power BI Service license needed for pilot; .pbix file opened manually refreshes in seconds via Import mode |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.x | Engine creation for `pandas.to_sql` | Use only as the engine factory for `to_sql`; pass `fast_executemany=True` to the pyodbc creator; do NOT use ORM or session-based patterns — direct SQL is cleaner for ETL |
| python-dotenv | 1.x | Load credentials from `.env` | Same pattern as existing tools — credentials stay in `.env`, never in scripts |
| logging (stdlib) | stdlib | Structured run logs | Write to rotating log file (e.g. `etl_YYYY-MM-DD.log`); no external logging framework needed at this scale |
| pywin32 | 306 | Windows Task Scheduler integration | Only needed if you want to register/update Task Scheduler entries from Python; optional — manual Task Scheduler setup is fine for a single job |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ODBC Driver 17 for SQL Server | pyodbc connection driver | Already installed (confirmed working in existing codebase); do NOT upgrade to ODBC Driver 18 without testing — Driver 18 enables `Encrypt=yes` by default which may require cert changes on this server |
| SSMS | Schema inspection, query development | Use to design and validate `raw`/`core`/`report` schema DDL before encoding it in Python |
| VS Code | Script editing | Consistent with project |

---

## Installation

```bash
# Already in requirements.txt for this project — confirm versions:
pip install pyodbc==5.3.0
pip install pandas==2.3.3
pip install sqlalchemy==2.0.36
pip install python-dotenv==1.0.0
```

No new dependencies that conflict with existing tools. Add to `requirements.txt` alongside existing entries.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pyodbc direct | pymssql | Never for this project — pymssql is effectively unmaintained; pyodbc with ODBC Driver 17 is the Microsoft-recommended path |
| pandas 2.x | pandas 3.0 | When Python 3.11+ is confirmed baseline and you have time to validate 2.x → 3.0 migration; not now |
| Windows Task Scheduler | SQL Server Agent | SQL Server Agent is available on Standard edition but correct for multi-step SQL-native pipelines; for a Python script that owns its own logic, Task Scheduler is simpler and doesn't require SQL Server restart to update |
| Power BI Desktop (manual refresh) | Power BI Service + Gateway | Use Service + Gateway when management wants web-accessible dashboards shared across the company; requires Pro license (check with Lebon IT whether M365 plan includes it) |
| Raw pyodbc + SQLAlchemy for writes | SSIS | SSIS is appropriate for large enterprises with dedicated BI teams and complex multi-system integration; overkill for a 50-person company with a single Python developer; no existing SSIS skillset |
| Raw pyodbc + SQLAlchemy for writes | dbt | dbt is an ELT transform layer for cloud data warehouses (Snowflake, BigQuery, Redshift); it does not extract or move data and has no advantage over SQL views in SQL Server on-premises |
| Raw pyodbc + SQLAlchemy for writes | Azure Data Factory | Cloud-only; violates the on-premises constraint; introduces Azure subscription cost |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SSIS | Requires SQL Server Data Tools, has its own XML-based package format, and needs a DBA to maintain; zero benefit over Python at this scale | Python + pyodbc |
| dbt | Designed for cloud warehouses; does not extract data; adds a YAML/Jinja/Python project structure that is heavier than the problem justifies | SQL views in the `report` schema |
| Azure Data Factory | Cloud service; violates on-premises constraint; monthly cost | Python + Task Scheduler |
| ODBC Driver 18 (without testing) | Enables `Encrypt=yes` by default; SQL Server 2016 without proper TLS certs will refuse connections with a certificate trust error | Keep ODBC Driver 17 unless you configure TLS or add `TrustServerCertificate=yes` to connection string |
| pandas 3.0 | Breaking changes from 2.x (Copy-on-Write is now default; several APIs changed); not worth the migration risk during ETL build phase | pandas 2.3.x |
| DirectQuery mode in Power BI | Sends a live query to SQL Server on every visual interaction; requires the laptop to have VPN active to open the report; kills usability for management; Standard Edition limits parallelism (DOP=2) which makes query performance unpredictable | Import mode with nightly scheduled refresh |
| Power BI Service (without license check) | Requires Power BI Pro license per user for sharing; on-premises refresh requires an always-on gateway server; don't assume M365 Business Basic includes it — verify with Lebon IT | Power BI Desktop for pilot phase; decide Service after pilot validates value |
| Airflow / Prefect | Orchestration frameworks designed for multi-pipeline, multi-team environments; require their own server/daemon; massively over-engineered for a single nightly Python script | Windows Task Scheduler + Python logging |

---

## Key Architectural Decisions with Rationale

### Decision 1: Python ETL, not SQL Server Agent T-SQL jobs

Write ETL logic in Python, triggered by Windows Task Scheduler. Not as stored procedures or SSIS packages.

**Why:** The team already writes and maintains Python. T-SQL procedural code (cursors, temp tables, multi-step jobs) is harder to read, harder to debug, and harder to version-control. Python gives you a full diff history in git, real error messages, and the ability to add logging, retries, and alerting later without touching the database.

### Decision 2: Three-schema architecture in one database

`raw` (daily snapshots with `snapshot_date`), `core` (facts + dimensions), `report` (views only).

**Why:** Separates concerns without separate databases. `raw` is append-only — reprocessing is always possible. `core` holds transformed facts. `report` is pure SQL views — Power BI connects here and the view definition IS the business logic, readable by anyone with SSMS.

### Decision 3: Import mode in Power BI, not DirectQuery

Power BI reads from `report` views once (on refresh), caches data in the .pbix file's internal Vertipaq engine.

**Why:** For nacalculatie and operational KPIs on ETO data, data is never real-time by nature (timesheets are logged with a day's lag anyway). Import mode reports open instantly without a VPN connection. DirectQuery would require VPN active whenever someone opens the report AND would hammer the production-adjacent SQL Server instance on every click. Import mode is the right trade-off at this scale.

### Decision 4: pyodbc `fast_executemany=True` for writes

When writing transformed rows from `core` back to SQL Server, use `fast_executemany=True` via the SQLAlchemy engine creator.

**Why:** Nightly ETL writes thousands (not millions) of rows. `fast_executemany` batches all parameter rows in a single ODBC call, giving 10-15x speedup over row-by-row inserts with minimal code change. No BCP, no temp files, no extra tooling.

---

## SQL Server 2016 Standard Edition — Confirmed Capabilities

These features are available in Standard Edition (confirmed after SP1) and are safe to use in this project:

| Feature | Available in Standard SP1? | Notes |
|---------|---------------------------|-------|
| Columnstore indexes | Yes (limited) | DOP capped at 2; columnstore cache capped at 32GB — irrelevant at this data size |
| Table partitioning | Yes | Useful for partitioning `raw` by `snapshot_date` if table grows large |
| Change Data Capture (CDC) | Yes | Available but not needed for nightly full-snapshot ETL |
| Database snapshots | Yes | Useful for point-in-time read of `Spinnekop Live 2` during ETL run |
| SQL Server Agent | Yes | Available but Windows Task Scheduler preferred for this use case |
| In-Memory OLTP | Yes (limited) | Not needed |
| Max database size | 524 PB (no practical limit) | Standard edition has no database size cap; only RAM capped at 128GB buffer pool |
| SSIS (Integration Services) | Separate install | Available but not recommended — see "What NOT to Use" |

**Key constraint:** SQL Server 2016 reached end of mainstream support in July 2021 and extended support in July 2026. No new features, security patches only until mid-2026. The reporting database workload is read-only against production, so this risk is contained. Plan to flag this in a future milestone.

---

## Power BI Refresh Path

| Scenario | What's Required | Confidence |
|----------|----------------|------------|
| Pilot: Rik opens .pbix on his laptop, clicks Refresh | VPN active + Power BI Desktop installed | HIGH — works today |
| Sharing with Francis/Mathieu as .pbix file | Email/Teams the .pbix; they open in Desktop | HIGH — free, no license needed |
| Sharing via Power BI Service (web URL) | Power BI Pro license per user + on-premises data gateway server | MEDIUM — verify M365 plan with Lebon IT before committing to this path |
| Automated nightly refresh in Power BI Service | Same as above; gateway must be always-on | LOW confidence on feasibility — verify license before designing around it |

**Recommendation for pilot:** Start with Power BI Desktop + manual refresh on demand. The nightly ETL writes to `Spinnekop_Reporting`; Rik opens the .pbix and hits Refresh before showing it. This has zero additional infrastructure. Decide on Service after the pilot proves value to management.

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|----------------|-------|
| pyodbc 5.3.0 | Python 3.8–3.14 | Wheels available for Windows; confirmed working on this machine |
| pandas 2.3.x | Python 3.9–3.14 | Pin to 2.x; avoid 3.0 for now |
| SQLAlchemy 2.0.36 | pyodbc 5.x | Use `mssql+pyodbc://` dialect; set `fast_executemany=True` in `create_engine()` |
| ODBC Driver 17 | SQL Server 2008–2022 | Confirmed working against `10.0.1.5\RIDDERIQ`; do not upgrade to Driver 18 without testing |
| Python 3.11/3.12 | Windows 11 | Use same Python version as existing tools to avoid virtualenv fragmentation |

---

## Connection String Pattern (for ETL scripts)

```python
import os
import pyodbc
import sqlalchemy

# Source (read-only)
SOURCE_CONN = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    "DATABASE=Spinnekop Live 2;"
    f"UID={os.getenv('SQL_USER')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "Trusted_Connection=no;"
    "Connection Timeout=10;"
)

# Reporting DB (write) — via SQLAlchemy for pandas to_sql
REPORT_ENGINE = sqlalchemy.create_engine(
    "mssql+pyodbc:///?odbc_connect=" + SOURCE_CONN.replace("Spinnekop Live 2", "Spinnekop_Reporting"),
    fast_executemany=True,
)
```

Credentials from `.env` only — same pattern as existing BOM Import Tool (`app_config.py`).

---

## Sources

- pyodbc 5.3.0 on PyPI — [https://pypi.org/project/pyodbc/](https://pypi.org/project/pyodbc/) (HIGH)
- pandas 2.3.x release notes — [https://pandas.pydata.org/docs/dev/whatsnew/v2.3.3.html](https://pandas.pydata.org/docs/dev/whatsnew/v2.3.3.html) (HIGH)
- SQLAlchemy 2.0 MSSQL dialect — [https://docs.sqlalchemy.org/en/20/dialects/mssql.html](https://docs.sqlalchemy.org/en/20/dialects/mssql.html) (HIGH)
- SQL Server 2016 Standard SP1 feature additions — [Brent Ozar: Standard Edition features](https://www.brentozar.com/archive/2016/11/sql-server-2016-standard-edition-now-many-enterprise-edition-features/) (MEDIUM, verified against Microsoft Tech Community blog)
- SQL Server Agent edition availability — [Microsoft Learn: SQL Server Agent](https://learn.microsoft.com/en-us/ssms/agent/sql-server-agent) (HIGH)
- Power BI DirectQuery vs Import mode — [Microsoft Learn: DirectQuery in Power BI](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-directquery-about) (HIGH)
- Power BI on-premises gateway requirement — [Microsoft Learn: Data refresh in Power BI](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-data) (HIGH)
- pyodbc fast_executemany insert performance — [hotglue.com benchmark](https://hotglue.com/blog/optimizing-microsoft-sql-insert-speed-in-python) (MEDIUM)
- Windows Task Scheduler vs SQL Server Agent — [SQLServerCentral community thread](https://www.sqlservercentral.com/forums/topic/sql-agent-vs-task-scheduler) (MEDIUM)

---

*Stack research for: Spinnekop v4.0 Rapporterings-DB (nightly ETL + Power BI)*
*Researched: 2026-03-19*
