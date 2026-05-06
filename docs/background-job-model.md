# Background Job Model

CarbonOps-Parser is intended to run as a background ingestion service for scheduled carbon factor source ingestion and parsing. The service evaluates source-specific schedules, checks whether source documents changed, archives raw files when needed, and records import metadata for each run.

This document defines the Phase 1 job and scheduling model at design level. It does not define worker code, scheduler code, parser code, database runtime behavior, ingestion logic, or deployment-specific retry mechanics.

Related documentation:

- [Configuration Model](configuration-model.md)
- [Database Startup](database-startup.md)
- [Database Model](database-model.md)
- [Source Support](source-support.md)
- [Configuration Example](../config/carbonops.config.example.yaml)

## Service Purpose

The background service coordinates the ingestion workflow for configured source families:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

Each source family has an independent configuration section, schedule, source version/hash check, raw archive layout, parser, validation rules, source-specific persistence target, and import metadata. A schedule for one source should not force another source to run.

The service is responsible for orchestration only. Source-specific parsers, validation rules, persistence mapping, and database startup behavior remain separate implementation concerns.

## Service Lifecycle

The full service lifecycle is:

1. Start the background service process.
2. Read configuration.
3. Validate the configured database provider.
4. Connect to PostgreSQL.
5. Ensure the required schema and tables exist.
6. Initialize configured source schedules.
7. Evaluate source due times.
8. Acquire a source-aware single-instance lock when a source is due.
9. Check the source version/hash.
10. Skip unchanged source versions/hashes.
11. Download changed source files.
12. Archive downloaded raw files.
13. Parse source-specific structures.
14. Validate parsed records.
15. Persist shared ingestion metadata and source-specific records.
16. Store import summary counts, validation issues, and final run status.
17. Release the source lock.
18. Continue evaluating future source due times until shutdown.

Shutdown should stop accepting new due work and allow active work to record a final state where possible. Exact shutdown mechanics are implementation-specific and deferred.

## Startup Order

Startup order is explicit and mandatory:

1. Read configuration.
2. Validate the database provider.
3. Connect to PostgreSQL.
4. Ensure schema/tables exist.
5. Initialize source schedules.
6. Evaluate source due times.
7. Run source ingestion only after the database is ready.

The service must not download, parse, validate, persist source data, or create import summaries before the PostgreSQL schema is available. See [Database Startup](database-startup.md) for the startup contract.

## Database Readiness Requirement

Phase 1 implements PostgreSQL as the persistence target. The conceptual configuration model recognizes `postgres`, `mysql`, and `mssql`, but Phase 1 must fail fast for any provider other than `postgres`.

Database readiness means the service has:

- Validated that the configured provider is `postgres`.
- Connected to PostgreSQL.
- Ensured shared ingestion metadata tables exist.
- Ensured source-specific DEFRA/DESNZ, GHG Protocol, and IPCC EFDB tables exist.

Source schedule evaluation may be initialized only after this readiness check succeeds.

## Source-Specific Schedules

Each source family has its own schedule. Schedules should support daily, weekly, monthly, and yearly periods with explicit time and timezone settings. A source is due only when its own schedule says it is due.

Example Phase 1 schedules are:

| Source family | Example schedule |
| --- | --- |
| GHG Protocol | Monthly at 04:00 UTC |
| DEFRA/DESNZ | Yearly at 04:30 UTC |
| IPCC EFDB | Monthly at 05:00 UTC |

These schedules are examples and can be changed by configuration. The shared configuration example is [config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml), and the conceptual schedule fields are documented in [Configuration Model](configuration-model.md).

## Source Schedule Evaluation

Schedule evaluation should:

- Load only enabled sources.
- Evaluate each source independently.
- Use the configured period, interval, day, time, and timezone.
- Determine whether a source is due for a check.
- Avoid running ingestion for sources that are not due.
- Avoid running ingestion before database readiness has completed.

When a source is due, the service moves into the source check and import lifecycle for that source only.

## Source Version/Hash Check

When a source is due, the service checks whether the latest source version or raw file hash differs from what is already stored in shared ingestion metadata.

The version/hash check should use source-specific check and download configuration. The exact source discovery mechanics are implementation-specific and may differ by source family.

## Duplicate Import Skipping

Imports should be idempotent by source version and content hash.

If the same source version/hash already exists, the import is skipped. Skipped imports should still be visible through import/run metadata where appropriate so operators can distinguish "checked and unchanged" from "not checked".

The recommended duplicate policy is `skip_if_same_hash`.

## Raw File Archive Boundary

Downloaded source files should be archived in the configured raw archive path. Raw file contents should not be stored directly in PostgreSQL tables.

PostgreSQL stores raw file metadata, such as source/version references, file path, file name, content type, size, hash, and downloaded timestamp. See [Database Model](database-model.md) for the shared metadata table responsibilities.

The archive boundary is:

- Downloaded file bytes belong in the raw archive path.
- File metadata and hashes belong in PostgreSQL.
- Parser input should come from the archived raw file or the downloaded file before archive handoff, depending on implementation design.
- Archive layout details are source-specific and may be refined during source discovery.

## Parser, Validator, and Persistence Boundary

The background service coordinates parser, validator, and persistence steps but should keep their responsibilities separate:

- Parser: reads the source-specific raw file structure and produces source-specific records.
- Validator: checks parsed records and records warnings or errors as import results.
- Persistence: writes shared ingestion metadata and source-specific master/detail records to PostgreSQL.

Phase 1 keeps source-specific records in `ghg_*`, `defra_*`, and `ipcc_*` table groups rather than forcing all sources into one canonical factor table. See [Source Support](source-support.md) and [Database Model](database-model.md).


## Job Lifecycle

At a high level, a scheduled job should:

1. Resolve the configured source.
2. Confirm the source is enabled and due.
3. Acquire the source-aware lock.
4. Record the run as `pending`.
5. Move to `checking` while checking the latest source version/hash.
6. Move to `skipped` if the same version/hash already exists.
7. Move to `downloaded` after a changed source file is downloaded and archived.
8. Move to `parsing` while parsing, validating, and preparing records.
9. Move to `completed` after metadata, source-specific records, summary counts, and validation issues are stored.
10. Move to `failed` when a source check, download, archive, parse, validation, or persistence boundary cannot complete.
11. Release the source-aware lock.

The status transitions above are conceptual. Implementations may persist intermediate records in language-appropriate ways as long as the resulting import/run metadata remains understandable.

## Import Run Status Model

Import runs should use these design-level statuses:

| Status | Meaning |
| --- | --- |
| `pending` | The service has identified work for a source and created or prepared run metadata before active checking starts. |
| `checking` | The service is checking source version/hash metadata to decide whether a download/import is needed. |
| `downloaded` | A changed source file has been downloaded and archived, and raw file metadata can be associated with the run. |
| `parsing` | The archived source file is being parsed, validated, and prepared for persistence. |
| `completed` | The import completed and summary metadata was stored. Validation warnings may still be recorded. |
| `skipped` | The source was checked, but the same version/hash already existed, so no duplicate import was performed. |
| `failed` | The run could not complete. Error summary metadata and validation issues should be recorded where available. |

Skipped runs should preserve enough metadata to explain why no import occurred, including the source identity and detected version/hash where available.

## Import Summary Behavior

Each import run should store summary metadata that makes the outcome visible without reading source-specific tables directly.

Summary metadata should include, where available:

- Source identity.
- Source version/hash.
- Final run status.
- Start and completion timestamps.
- Raw file hash for downloaded files.
- Total, valid, warning, error, and skipped row counts.
- Error summary when a run fails.
- Validation issues linked to the import run.

Validation warnings or data quality issues do not necessarily make a run fail. The distinction between warnings and errors should be recorded in import metadata and validation issue records.

## Idempotency

Imports should be idempotent by source version and content hash.

The recommended duplicate policy is `skip_if_same_hash`. If a source version and file hash already exist, the job should record or report that no import was needed and avoid duplicate persistence.

## Failure Handling

Failure handling is defined at design level:

- Source check failures should be recorded against the import run when a run exists.
- Download or archive failures should leave the run in `failed` with an error summary where available.
- Parsing and data validation errors should be recorded as import results and validation issues.
- Persistence failures should leave enough run metadata to diagnose the failed boundary where possible.
- A failed run should release any source-aware lock after recording its outcome.

Exact exception types, logging shape, transaction boundaries, and shutdown behavior are deferred to implementation tasks.

## Retry Boundary

Retries apply to transient source check and download failures. Examples include temporary network failures, source endpoint timeouts, or recoverable download interruptions.

Parsing and data validation errors should be recorded as import results instead of being retried blindly. Persistence retry behavior depends on implementation-specific database transaction handling and is not defined here.

The exact deployment-specific retry strategy is not defined in Phase 1. Configuration may expose retry counts and delays, but final runtime behavior is deferred.

## Single-Instance Lock Concept

The database model includes `carbon_job_locks` for a single-instance lock concept. The design goal is to prevent overlapping imports for the same source when a previous run is still active.

The lock concept should be:

- Source-aware, so GHG Protocol, DEFRA/DESNZ, and IPCC EFDB can be coordinated independently.
- Used before starting source-specific check/download/import work.
- Released when the source run completes, skips, fails, or shuts down cleanly.
- Protected by timeout behavior so stale locks do not block a source forever.

Phase 1 documentation defines the lock concept only. Lock acquisition, renewal, stale lock cleanup, clock handling, and conflict behavior are deferred to implementation tasks.
