# PH-018 Real Production-Ready Ingestion Contract

This document replaces the previous test-harness-oriented production-ready
interpretation with the project owner's required production-ready definition.

It is documentation only. It does not implement runtime code, add credentials,
connect to PostgreSQL, download source files, parse live data, write records,
start a scheduler, merge pull requests, approve pull requests, close issues,
delete branches, delete worktrees, or claim unrelated product tasks.

## Production-Ready Definition

CarbonOps-Parser is production-ready only when the application can perform this
complete operational loop:

1. Start the application.
2. Load approved runtime configuration.
3. Check PostgreSQL connectivity and schema state.
4. Create missing required source-specific master/detail tables safely.
5. For GHG Protocol, DEFRA/DESNZ, and IPCC EFDB, read the latest successfully
   ingested year from PostgreSQL.
6. If no year has been ingested for a source family, target the configured
   initial year. The default initial year is `2024`.
7. If a year has been ingested, target `latest_year + 1` for that source family.
8. Download real target-year source data when the source family has published
   that year.
9. Archive the raw source artifact and record archive metadata.
10. Parse the archived artifact.
11. Validate parsed records.
12. Insert accepted records into PostgreSQL source-specific master/detail tables.
13. Update the source family's latest-ingested year only after successful insert.
14. Repeat on the configured schedule.

The expected near-term cycle is:

- First successful run ingests `2024`.
- Next successful run ingests `2025`.
- Next successful run ingests `2026`.
- A later run attempts `2027` and returns `no_available_source_year` when the
  source has not published that year.

`no_available_source_year` is a safe no-op. It must not insert source records,
must not update latest-year state, and must be visible in run output.

## Current Status

The repository must not be described as production-ready under this definition
until the follow-up implementation tasks below and final validation are complete.

PH-017 Docker PostgreSQL validation evidence is useful test-harness evidence,
but it is not sufficient for this production-ready definition because this
definition requires real source downloads, source-specific master/detail
persistence, startup schema creation, latest-year-driven scheduling, and
idempotent repeated runtime cycles.

## Required Runtime Configuration

Production runtime configuration must define:

- PostgreSQL connection ownership and non-secret connection fields.
- PostgreSQL secret boundary for the password or approved credential mechanism.
- PostgreSQL schema name.
- Archive root for raw downloaded source artifacts.
- Enabled source families from `ghg_protocol`, `defra_desnz`, and `ipcc_efdb`.
- Initial year, defaulting to `2024`.
- Cycle interval or schedule.
- Max target year behavior.
- Schema bootstrap mode for additive creation of missing required objects.
- Runtime no-op behavior when a target year is unavailable.
- Logging level and diagnostics redaction policy.

Raw DSNs, passwords, tokens, and source credentials must not be committed.

## Shared Tables

Shared tables exist only where they support source-specific ingestion. They do
not replace source-specific master/detail persistence.

### `ingestion_runs`

Purpose: records one application cycle or source-family attempt.

Required columns:

- `ingestion_run_id uuid primary key`
- `cycle_id text not null`
- `source_family text not null`
- `target_year integer not null`
- `run_status text not null`
- `started_at timestamp with time zone not null`
- `completed_at timestamp with time zone null`
- `error_code text null`
- `error_message text null`
- `metadata jsonb not null`

Required constraints and indexes:

- Index on `(source_family, target_year, started_at)`.
- `run_status` must use explicit values such as `started`, `completed`,
  `completed_noop`, `failed_validation`, and `failed_runtime`.

### `source_artifacts`

Purpose: records downloaded raw source artifacts stored under the configured
archive root.

Required columns:

- `source_artifact_id uuid primary key`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null`
- `source_year integer not null`
- `source_version text not null`
- `source_archive_version text null`
- `source_url text not null`
- `archive_path text not null`
- `content_type text null`
- `byte_size bigint null`
- `sha256 text not null`
- `downloaded_at timestamp with time zone not null`
- `metadata jsonb not null`

Required constraints and indexes:

- Unique `(source_family, source_year, source_version, sha256)`.
- Index on `(source_family, source_year)`.

### `source_family_year_states`

Purpose: records successfully completed year ingestion by source family.

Required columns:

- `source_family text not null`
- `ingested_year integer not null`
- `source_version text not null`
- `source_artifact_id uuid not null references source_artifacts`
- `completed_ingestion_run_id uuid not null references ingestion_runs`
- `completed_at timestamp with time zone not null`
- `metadata jsonb not null`

Required constraints and indexes:

- Primary key or unique constraint on `(source_family, ingested_year)`.
- Index on `(source_family, ingested_year desc)`.

Year state is updated only after source-specific master/detail insert commits.

### `ingestion_validation_issues`

Purpose: records structured parse, validation, and persistence issues.

Required columns:

- `validation_issue_id uuid primary key`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null`
- `source_year integer not null`
- `table_name text null`
- `record_external_key text null`
- `source_row_reference text null`
- `severity text not null`
- `code text not null`
- `message text not null`
- `field_name text null`
- `raw_value text null`
- `created_at timestamp with time zone not null`

## Source-Specific Persistence Rule

Production persistence is source-specific. The source-specific master/detail
tables below are the system of record for Phase 1 production ingestion.

The existing normalized-only persistence path is not sufficient for production
readiness under PH-018. A normalized projection may be added later for search or
cross-source lookup, but it must be derived from source-specific master/detail
records or explicitly linked to them. It must not be the only production
persistence model.

## GHG Protocol Tables

### `ghg_protocol_masters`

Purpose: one row per logical GHG Protocol source-year record group, workbook
tool, sheet section, or other parser-owned master grouping.

Required columns:

- `ghg_protocol_master_id uuid primary key`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'ghg_protocol'`
- `source_year integer not null`
- `source_version text not null`
- `source_archive_version text null`
- `master_external_key text not null`
- `tool_name text null`
- `worksheet_name text null`
- `category_name text null`
- `subcategory_name text null`
- `region text null`
- `lifecycle_status text not null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(source_family, source_year, source_version, master_external_key)`.
- Index on `(source_family, source_year)`.
- Index on `source_artifact_id`.

### `ghg_protocol_details`

Purpose: one row per parsed GHG Protocol factor value or factor component.

Required columns:

- `ghg_protocol_detail_id uuid primary key`
- `ghg_protocol_master_id uuid not null references ghg_protocol_masters`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'ghg_protocol'`
- `source_year integer not null`
- `source_version text not null`
- `detail_external_key text not null`
- `source_row_reference text null`
- `activity_name text null`
- `activity_unit text null`
- `fuel_or_material text null`
- `gas text null`
- `factor_value numeric not null`
- `factor_unit text not null`
- `co2e_factor_value numeric null`
- `quality_flag text null`
- `notes text null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(ghg_protocol_master_id, detail_external_key)`.
- Unique `(source_family, source_year, source_version, detail_external_key)`.
- Index on `(source_family, source_year)`.

## DEFRA/DESNZ Tables

### `defra_desnz_masters`

Purpose: one row per logical DEFRA/DESNZ source-year factor set, category,
sheet, tab, or parser-owned grouping.

Required columns:

- `defra_desnz_master_id uuid primary key`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'defra_desnz'`
- `source_year integer not null`
- `source_version text not null`
- `source_archive_version text null`
- `master_external_key text not null`
- `dataset_name text null`
- `worksheet_name text null`
- `category_name text null`
- `subcategory_name text null`
- `scope_hint text null`
- `region text null`
- `lifecycle_status text not null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(source_family, source_year, source_version, master_external_key)`.
- Index on `(source_family, source_year)`.
- Index on `source_artifact_id`.

### `defra_desnz_details`

Purpose: one row per parsed DEFRA/DESNZ factor value or factor component.

Required columns:

- `defra_desnz_detail_id uuid primary key`
- `defra_desnz_master_id uuid not null references defra_desnz_masters`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'defra_desnz'`
- `source_year integer not null`
- `source_version text not null`
- `detail_external_key text not null`
- `source_row_reference text null`
- `activity_name text null`
- `activity_unit text null`
- `gas text null`
- `factor_value numeric not null`
- `factor_unit text not null`
- `conversion_factor_type text null`
- `quality_flag text null`
- `notes text null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(defra_desnz_master_id, detail_external_key)`.
- Unique `(source_family, source_year, source_version, detail_external_key)`.
- Index on `(source_family, source_year)`.

## IPCC EFDB Tables

### `ipcc_efdb_masters`

Purpose: one row per logical IPCC EFDB source-year sector, category, reference,
or parser-owned factor record grouping.

Required columns:

- `ipcc_efdb_master_id uuid primary key`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'ipcc_efdb'`
- `source_year integer not null`
- `source_version text not null`
- `source_archive_version text null`
- `master_external_key text not null`
- `sector_code text null`
- `sector_name text null`
- `category_code text null`
- `category_name text null`
- `reference_title text null`
- `reference_year integer null`
- `region text null`
- `country text null`
- `lifecycle_status text not null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(source_family, source_year, source_version, master_external_key)`.
- Index on `(source_family, source_year)`.
- Index on `source_artifact_id`.

### `ipcc_efdb_details`

Purpose: one row per parsed IPCC EFDB factor value, default/min/max value, or
measurement component.

Required columns:

- `ipcc_efdb_detail_id uuid primary key`
- `ipcc_efdb_master_id uuid not null references ipcc_efdb_masters`
- `source_artifact_id uuid not null references source_artifacts`
- `ingestion_run_id uuid not null references ingestion_runs`
- `source_family text not null default 'ipcc_efdb'`
- `source_year integer not null`
- `source_version text not null`
- `detail_external_key text not null`
- `source_row_reference text null`
- `parameter_name text null`
- `activity_name text null`
- `technology_or_practice text null`
- `gas text null`
- `factor_value numeric null`
- `default_value numeric null`
- `min_value numeric null`
- `max_value numeric null`
- `factor_unit text not null`
- `uncertainty text null`
- `data_quality text null`
- `notes text null`
- `record_checksum_sha256 text not null`
- `metadata jsonb not null`
- `created_at timestamp with time zone not null`
- `updated_at timestamp with time zone not null`

Required constraints and indexes:

- Unique `(ipcc_efdb_master_id, detail_external_key)`.
- Unique `(source_family, source_year, source_version, detail_external_key)`.
- Index on `(source_family, source_year)`.

## Idempotency Keys

Every source-specific master row must have a deterministic
`master_external_key` built from:

- `source_family`
- `source_year`
- `source_version`
- source artifact identity or source archive version
- source-specific logical grouping identity

Every source-specific detail row must have a deterministic `detail_external_key`
built from:

- `source_family`
- `source_year`
- `source_version`
- parent `master_external_key`
- source row reference or parser-stable row identity
- factor field identity when one source row contains multiple factor values

`record_checksum_sha256` must hash the canonical persisted record payload used
for conflict detection. A repeated run with the same idempotency key and same
checksum is a duplicate no-op. A repeated run with the same idempotency key and
a different checksum is a conflict and must fail or require a future reviewed
replacement policy.

## Runtime Cycle Behavior

At application startup:

1. Load configuration.
2. Validate PostgreSQL provider and required configuration.
3. Open a PostgreSQL connection using the approved credential boundary.
4. Check the required schema and tables.
5. Create missing tables and indexes using additive, idempotent DDL when schema
   bootstrap is enabled.
6. Stop startup if PostgreSQL is unavailable, schema bootstrap is disabled with
   missing objects, or incompatible existing objects are detected.
7. Start the configured ingestion scheduler only after schema readiness passes.

On each scheduled cycle, each enabled source family runs independently:

1. Read `max(ingested_year)` from `source_family_year_states`.
2. Select `target_year = initial_year` when no year exists.
3. Select `target_year = latest_year + 1` when a year exists.
4. Apply configured max target year behavior.
5. Discover whether real source data exists for `target_year`.
6. If unavailable, record `no_available_source_year` in run output only.
7. If available, download and archive the source artifact.
8. Parse the archived artifact.
9. Validate parsed records.
10. Insert source-specific master/detail rows in one reviewed transaction
    boundary.
11. Commit source-specific rows and then update `source_family_year_states`.
12. Report inserted, duplicate, validation-failed, and no-op counts.

The scheduler must prevent overlapping cycles for the same source family.
Repeated cycles must be idempotent.

## Follow-Up Implementation Tasks

PH-018 is complete only when this contract is documented. Implementation remains
future work.

Required follow-up tasks:

1. Replace the current normalized-only PostgreSQL runtime schema with the
   source-specific master/detail schema in this contract.
2. Implement additive startup schema bootstrap for the shared and
   source-specific tables.
3. Implement runtime configuration for PostgreSQL, archive root, enabled source
   families, initial year, cycle schedule, and max target year behavior.
4. Implement latest-successful-year lookup and year-state update semantics.
5. Implement GHG Protocol real source discovery and target-year download from
   2024 onward.
6. Implement DEFRA/DESNZ real source discovery and target-year download from
   2024 onward.
7. Implement IPCC EFDB real source discovery and target-year download from 2024
   onward.
8. Implement raw artifact archive layout and metadata persistence.
9. Implement source-specific parsers that write to the source-specific
   master/detail model.
10. Implement idempotent insert and conflict handling for source-specific
    tables.
11. Implement scheduled runtime cycles with overlap prevention and structured
    no-op reporting.
12. Add Docker PostgreSQL integration tests for startup bootstrap, 2024 initial
    ingestion, 2025/2026 next-year progression, 2027 unavailable no-op,
    idempotent replay, and conflict handling.
13. Add final validation before any production-ready claim is restored.

## Non-Goals

This task does not:

- Implement runtime code.
- Implement live source downloads.
- Implement parser changes.
- Implement PostgreSQL DDL changes.
- Add credentials.
- Claim production readiness.
- Claim source-owner, factor, unit-conversion, legal, compliance, or
  carbon-accounting correctness.
- Merge, approve, or close any pull request or issue.

## PR Body Footer

The pull request body for PH-018 must end with:

```text
Task-ID: PH-018
Task-Issue: #594
```

Task-ID: PH-018
Task-Issue: #594
