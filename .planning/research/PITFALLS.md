# Pitfalls Research

**Domain:** ERP Reporting Database — SQL Server ETL + Power BI (small company, on-premises)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH — ETL and data warehouse pitfalls are well-documented; specific findings for this exact stack (SQL Server 2016 + pyodbc + Task Scheduler + VPN) are verified across multiple sources.

---

## Critical Pitfalls

### Pitfall 1: Silent ETL Failure — No One Notices Until the Report Is Wrong

**What goes wrong:**
The nightly Task Scheduler job fails (VPN dropped, SQL timeout, Python exception) but nobody notices because Task Scheduler does not surface non-zero exit codes to any alert channel. Users open Power BI the next morning and see yesterday's data — or worse, three-day-old data. The problem is only discovered when a number looks wrong in a meeting.

**Why it happens:**
Task Scheduler's default behaviour is "run the task, show green if the process started". It does not distinguish between a Python script that exits 0 (success) and one that exits 1 (exception). Developers test the happy path, confirm the job runs, and ship it without wiring up failure reporting.

**How to avoid:**
- Write ETL run metadata to a control table in `Spinnekop_Reporting` on every execution: `etl_run_id`, `run_date`, `status` (success/fail), `rows_extracted`, `error_message`, `duration_seconds`.
- Add a Power BI "data freshness" card to every report page: `MAX(snapshot_date)` from any fact table. If it is not today, the report is stale — visible immediately.
- Redirect all stdout/stderr to a rotating log file: `python etl.py >> C:\logs\etl.log 2>&1` in the Task Scheduler action.
- Optionally: send a one-line email via `smtplib` on failure (can use existing Office 365 relay if Spinnekop has one).

**Warning signs:**
- `MAX(snapshot_date)` in Power BI lags more than one day.
- Log file has zero new lines after the expected run window.
- Task Scheduler History tab shows "Task completed" but last result code is non-zero (check the "Last Run Result" column — `0x1` means the script exited with an error).

**Phase to address:** ETL foundation phase (first working pipeline). Build the control table and freshness card before the first real stakeholder demo.

---

### Pitfall 2: VPN Drops Mid-Run, Leaving a Half-Written Raw Layer

**What goes wrong:**
The ETL extracts `R_TIMESHEETLINE` (potentially thousands of rows) over VPN. VPN disconnects halfway through. The Python script either hangs indefinitely waiting for the TCP connection to recover, or crashes with `OperationalError: HYT00`. The raw table now has a partial day's data — some rows from today, some from yesterday. The core layer processes it and produces wrong totals. With `snapshot_date` appended per run, re-running the ETL would duplicate rows.

**Why it happens:**
pyodbc connection pooling keeps stale connections alive after a VPN drop. The ODBC driver's default connection timeout is often 0 (unlimited), meaning a broken TCP socket can hang the script for 30+ minutes. VPN dropouts are a known reality on this project (documented in PROJECT.md constraints).

**How to avoid:**
- Set explicit timeouts in every connection string: `Connection Timeout=15;` (login) plus `cursor.timeout = 30` (query). Accept that the job will fail fast rather than hang.
- Wrap all ETL logic in a try/except that writes `status='FAILED'` to the control table before exiting with code 1.
- Use a `DELETE FROM raw.timesheetline WHERE snapshot_date = CAST(GETDATE() AS DATE)` at the start of each table's extract — before inserting. This makes the extract idempotent: re-running after a failure cleans up the partial write.
- Disable pyodbc connection pooling for the ETL script: `pyodbc.pooling = False` as the first line. This prevents stale pooled connections from being reused after a VPN reconnect.
- Do the VPN ping check (already established pattern in this codebase) before starting the ETL run.

**Warning signs:**
- Script runtime exceeds 3x its normal duration.
- Control table shows `status='RUNNING'` from more than 2 hours ago (stuck process).
- Row count in raw table does not match expected range for that day.

**Phase to address:** ETL foundation phase. The idempotency pattern must be baked in from the first table extracted — retrofitting it later is painful.

---

### Pitfall 3: ERP Schema Drift Breaks the Pipeline on the Next RidderIQ Update

**What goes wrong:**
RidderIQ is a vendor-managed ERP. Ridder Support pushes an update (this has already happened on this project — the server incident 2026-03-06 required a restore). An update renames a column, changes a data type (e.g., `INT` to `BIGINT`), or adds a `NOT NULL` column with no default. The Python ETL script that uses `SELECT col1, col2, col3 FROM R_TIMESHEETLINE` now either fails on the column reference or silently inserts wrong data because column positions shifted.

**Why it happens:**
ETL scripts typically hardcode column names and types. The source is a black-box ERP; you do not control its schema. Vendors rarely provide advance notice of schema changes.

**How to avoid:**
- Never use `SELECT *` into a raw table without immediately checking column count and types. Always `SELECT` named columns explicitly.
- Create a schema snapshot table: `raw.schema_snapshot (table_name, column_name, data_type, ordinal_position, snapshot_date)`. Populate it on each ETL run from `INFORMATION_SCHEMA.COLUMNS` on the source DB. Add a comparison step that alerts if column count or types changed since the last run.
- Design raw tables to mirror source schema exactly — no transformations. Transformations belong in core. This limits blast radius: if a source column changes, only the raw extract breaks, not the entire core/report layer.
- Keep a `scripts/ridderiq-schema-baseline.sql` file (committed) with the expected schema of each extracted table. Check it after every RidderIQ update.

**Warning signs:**
- RidderIQ update notification from Ridder Support.
- ETL run fails with `Invalid column name` or `Cannot insert NULL into column` errors.
- Schema snapshot comparison detects column count change.

**Phase to address:** ETL foundation phase (schema snapshot) + each phase that adds a new source table. After any RidderIQ update, run schema comparison before resuming ETL.

---

### Pitfall 4: Power BI Desktop Cannot Auto-Refresh — Gateway Is Required for Service Publishing

**What goes wrong:**
A Power BI Desktop `.pbix` file connects directly to `10.0.1.5\RIDDERIQ` via ODBC/DirectQuery or to `Spinnekop_Reporting` via Import mode. It works perfectly on the developer's laptop over VPN. When published to Power BI Service for sharing, scheduled refresh fails immediately because Power BI Service cannot reach an on-premises SQL Server without an On-Premises Data Gateway installed on a machine that is always on and always on the network.

**Why it happens:**
Power BI Service lives in Microsoft's cloud. It cannot reach `10.0.1.5` directly. This is a fundamental architecture requirement that is easy to miss when the only testing happens on a VPN-connected developer laptop.

**How to avoid:**
- The ETL-to-reporting-DB architecture this project uses is the correct mitigation: Power BI connects to `Spinnekop_Reporting` (which already has fresh data after each ETL run), not to the live ERP. This isolates Power BI from the production system.
- For Power BI Desktop (free) — no scheduled refresh at all. The file must be manually refreshed and re-opened. Acceptable for pilot/internal use.
- For Power BI Service sharing — requires either: (a) a Power BI Pro license + On-Premises Data Gateway installed on a machine on the Spinnekop network that is always on, or (b) publish from a machine that has the data embedded (Import mode, manual refresh cycle).
- Confirm M365 plan with Lebon IT before promising automated refresh to stakeholders. This is flagged in PROJECT.md as a known open question.

**Warning signs:**
- "Data source credentials" or "gateway not found" error in Power BI Service after publishing.
- Report shows data from the last manual refresh date, not today.

**Phase to address:** Power BI pilot phase. Validate gateway requirement before committing to a scheduled refresh SLA with Spinnekop.

---

### Pitfall 5: Reading Production ERP During Business Hours Causes Locking

**What goes wrong:**
The nightly ETL runs `SELECT` queries against `Spinnekop Live 2` while production users are active (especially if the nightly window is poorly timed or the ETL re-runs manually during the day). Long-running SELECT scans on large tables like `R_TIMESHEETLINE` or `R_PRODUCTIONORDER` acquire shared locks that block concurrent write operations in RidderIQ, causing the ERP to appear slow or hang for users.

**Why it happens:**
SQL Server's default `READ COMMITTED` isolation acquires shared locks on rows as they are read. A full-table scan holds many shared locks simultaneously. In SQL Server 2016, `READ_COMMITTED_SNAPSHOT` is off by default unless explicitly enabled; without it, readers and writers block each other.

**How to avoid:**
- Schedule the ETL run strictly outside business hours: e.g., 02:00 local time, with a maximum runtime guard.
- Use `READ UNCOMMITTED` (`NOLOCK` hint) on all source SELECT queries in the ETL, or enable `READ_COMMITTED_SNAPSHOT` isolation on `Spinnekop Live 2`. `NOLOCK` risks reading uncommitted data; for a nightly snapshot that acceptable — the alternative (blocking production) is worse. Document the choice explicitly.
- Never run ETL manually during business hours without warning.
- Keep ETL queries narrow: `SELECT` only the columns you need, use date filters to limit row scans.

**Warning signs:**
- RidderIQ users report slowness during ETL window.
- `sys.dm_exec_requests` on the source server shows blocked sessions during ETL run.
- ETL duration spikes on days with high ERP activity.

**Phase to address:** ETL foundation phase. Add `WITH (NOLOCK)` to all source queries from day one.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip the control/audit table in v1 | Faster to build | No visibility into failures; debugging is guesswork after 3 failed runs | Never — build it in the first phase, it takes 1 hour |
| Load all columns with `SELECT *` into raw | Less code to write | Any ERP update silently shifts column order or adds NULLs; data corrupts | Never — always name columns explicitly |
| Hardcode date filter as "yesterday" in ETL | Simple logic | If the job misses a night, that day's data is permanently lost | Never — use watermark from control table or parameterised date |
| Put business logic in Power BI DAX instead of SQL views | Faster first demo | Logic is invisible to SQL users; duplicated across reports; impossible to test | Acceptable for one-off calculations; never for reusable KPIs |
| Skip the `raw` layer, write directly to `core` | One fewer layer | Cannot replay/re-transform without re-extracting from ERP; schema drift kills you | Never — the raw layer is your disaster recovery |
| Use Power BI DirectQuery against the reporting DB | Always "live" data | Slow; every report interaction fires a SQL query; kills report UX for non-DBA-tuned models | Only if the dataset is too large for Import mode, which it is not at Spinnekop scale |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| pyodbc + SQL Server 2016 over VPN | Use default connection timeout (0 = unlimited); script hangs forever on VPN drop | Set `Connection Timeout=15` in connection string; set `cursor.timeout` per query |
| pyodbc connection pool | Reuse stale pooled connection after VPN reconnect; get cryptic `OperationalError` | Set `pyodbc.pooling = False` at script start for ETL use case |
| Power BI + on-premises SQL Server | Connect to live ERP in `.pbix`; works locally, breaks when published | Connect to `Spinnekop_Reporting` (the reporting DB) via Import mode; gateway handles the rest |
| Task Scheduler + Python | Use relative paths in the script; works in dev shell, fails in scheduler context | Use absolute paths everywhere; set Working Directory in the task action to the script folder |
| Task Scheduler service account | Run as user's personal account; breaks when user logs off or password changes | Create a dedicated local/domain service account; grant minimal SQL permissions on `Spinnekop_Reporting` only |
| SQL Server source + ODBC Driver | Mix ODBC Driver 17 and 18 across machines; Driver 18 enforces certificate by default | Pin to ODBC Driver 17 for SQL Server across all machines, or add `TrustServerCertificate=yes` for Driver 18 |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full daily snapshot of entire ERP tables | ETL takes 30 min at 10k rows; acceptable | Query time scales linearly; at 500k rows it takes hours | When `R_TIMESHEETLINE` accumulates 2+ years of data |
| No index on `snapshot_date` in raw tables | Fast inserts initially | Full scans on every Power BI refresh query once table has 100k+ rows | Around 50k-100k rows per table |
| No index on fact table join keys (VO number, employee ID) | Queries fast when dataset is small | Slow Power BI reports; users complain reports take 30+ seconds | When core layer has 12+ months of data |
| Date dimension generated in DAX (CALENDAR function) | Works for simple reports | Cannot join to raw/core layer in SQL; filters do not fold | When you need SQL-side date filtering for performance |

---

## Security Mistakes

Domain-specific security issues for an ERP reporting setup.

| Mistake | Risk | Prevention |
|---------|------|------------|
| ETL service account has `db_owner` on `Spinnekop Live 2` (production ERP) | A bug in ETL code could mutate or delete production ERP data | ETL account needs only `SELECT` on `Spinnekop Live 2`; `db_owner` only on `Spinnekop_Reporting` |
| SQL credentials hardcoded in Python script | `.py` file committed to git exposes `ridderadmin` password | Use `.env` file (already established pattern in this project); never commit credentials |
| Power BI `.pbix` file stored on SharePoint with embedded credentials | Anyone with file access can extract the connection string | Use Power BI Service with gateway for sharing; never share raw `.pbix` files with embedded credentials over SharePoint |
| `Spinnekop_Reporting` accessible to all domain users | Users can write ad-hoc SQL against reporting DB | Grant `SELECT` only on `report` schema to Power BI service account; lock down `raw` and `core` to ETL account only |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **ETL job:** Control table exists with run status — verify `SELECT TOP 1 * FROM raw.etl_run_log ORDER BY run_date DESC` returns a row for today.
- [ ] **ETL job:** Idempotency is tested — run the ETL twice for the same date and confirm row counts do not double in raw tables.
- [ ] **Power BI report:** Freshness card visible on every page — verify it shows today's date after ETL completes.
- [ ] **Power BI report:** Report works for a user who does NOT have VPN access — they connect to Power BI Service, not directly to SQL Server.
- [ ] **Schema drift detection:** Baseline SQL exists in repo — verify `scripts/ridderiq-schema-baseline.sql` captures all extracted tables.
- [ ] **Task Scheduler:** Job runs as service account, not personal account — verify by logging off and checking the task still runs at its scheduled time.
- [ ] **Date dimension:** Populated for at least 5 years forward from today — verify `SELECT MAX(date_key) FROM core.dim_date` is not in the past.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Silent ETL failure discovered 3 days later | MEDIUM | Delete raw rows for affected dates (`DELETE FROM raw.X WHERE snapshot_date BETWEEN ...`); re-run ETL with parameterised date range for each missed date |
| VPN dropped mid-run, partial raw data | LOW | Idempotency pattern handles it: re-run ETL for today; `DELETE` at start of extract clears the partial data before re-inserting |
| ERP schema change breaks ETL | MEDIUM | Fix column reference in Python; verify raw table schema still matches; re-run extract for the broken date; update `ridderiq-schema-baseline.sql` |
| Power BI Gateway offline, stale report | LOW | Re-run ETL manually; open Desktop `.pbix`, refresh, republish to Service |
| Core layer logic was wrong (business rule misunderstood) | HIGH | Raw layer is the safety net — re-run core transformation from raw without touching the ERP; correct the SQL view; validate against known correct numbers |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Silent ETL failure | ETL foundation (Phase 1) | Control table populated after first run; freshness card in pilot report |
| VPN mid-run failure | ETL foundation (Phase 1) | Idempotency test: run ETL twice same date, counts unchanged |
| ERP schema drift | ETL foundation (Phase 1) + every new table added | `ridderiq-schema-baseline.sql` committed; schema snapshot comparison runs nightly |
| Power BI gateway requirement | Power BI pilot phase | Test publish to PBI Service before stakeholder demo |
| Production ERP locking | ETL foundation (Phase 1) | All source queries use `WITH (NOLOCK)`; ETL scheduled 02:00 |
| Technical debt: no raw layer | Architecture decision (Phase 1) | `raw`, `core`, `report` schemas created before any data lands |
| Hardcoded credentials | ETL foundation (Phase 1) | `.env` pattern already established; verify no credentials in `.py` files |

---

## Sources

- [5 Critical ETL Pipeline Design Pitfalls to Avoid in 2026 — Airbyte](https://airbyte.com/data-engineering-resources/etl-pipeline-pitfalls-to-avoid) — MEDIUM confidence (WebSearch)
- [How to Get ETL Horribly Wrong — Red Gate Simple Talk](https://www.red-gate.com/simple-talk/databases/sql-server/bi-sql-server/how-to-get-etl-horribly-wrong/) — MEDIUM confidence (WebSearch, practitioner post-mortem)
- [Transaction Locking and Row Versioning Guide — Microsoft Docs](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16) — HIGH confidence (official Microsoft documentation)
- [Configure Scheduled Refresh — Power BI Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-scheduled-refresh) — HIGH confidence (official Microsoft documentation)
- [Data Refresh in Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-data) — HIGH confidence (official Microsoft documentation)
- [pyodbc Connection Pool Timeout Issues — GitHub #734](https://github.com/mkleehammer/pyodbc/issues/734) — MEDIUM confidence (official issue tracker)
- [Why Your ETL Data Pipelines Keep Breaking — Weld Blog](https://weld.app/blog/why-data-pipelines-break) — LOW confidence (vendor blog, WebSearch only)
- [Schema Drift in ETL Pipelines — Integrate.io](https://www.integrate.io/blog/what-is-schema-drift-incident-count/) — LOW confidence (vendor blog, WebSearch only)
- [Achieving Seamless ETL Automation with Task Scheduler, Python and SQL — Medium](https://orokgospel.medium.com/achieving-seamless-etl-automation-with-windows-task-scheduler-python-and-sql-02f473860d66) — LOW confidence (community post)
- Project context: `.planning/PROJECT.md` — constraints section (VPN instability, no PowerShell Remoting, pyodbc over VPN already in use)

---
*Pitfalls research for: ERP reporting database, SQL Server ETL + Power BI, small company on-premises*
*Researched: 2026-03-19*
