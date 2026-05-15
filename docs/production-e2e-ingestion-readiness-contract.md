# Production E2E Ingestion Readiness Contract

This document defines the production end-to-end ingestion readiness contract for
CarbonOps-Parser.

It is documentation only. It does not implement runtime code, call live
endpoints, execute database operations, create credentials, download source
files, parse real upstream documents, validate factor correctness, or claim
production carbon-accounting correctness.

## Production Definition

For this project, production E2E ingestion means one run performs this
operational sequence:

1. Check PostgreSQL connectivity, schema state, and required tables.
2. Create missing required PostgreSQL tables safely if the configured runtime
   mode allows schema bootstrap.
3. For each selected source family, inspect PostgreSQL for the latest ingested
   source year.
4. If no data exists for that source family, select the configured initial year.
5. If data exists, calculate `next_year = latest_year + 1`.
6. Attempt source-specific discovery and download for `next_year` only.
7. If source data exists for `next_year`, download it, archive it, parse it,
   validate it, and insert accepted records into PostgreSQL.
8. If source data does not exist or is unavailable for `next_year`, do not fail
   the whole run; report `no_available_source_year`.
9. Return a run summary with per-family year state, action taken, inserted
   counts, skipped/no-op counts, validation failures, and failure details.

The default configured initial year is `2024`. A deployment may explicitly
configure a different initial year. The effective initial year must be visible in
run configuration and run output.

## Source Families

The contract applies to these Phase 1 source families:

- `ghg_protocol` for GHG Protocol.
- `defra_desnz` for DEFRA/DESNZ.
- `ipcc_efdb` for IPCC EFDB.

Each source family owns its own discovery, download, archive, parser,
validation, and PostgreSQL table mapping. A production E2E run must not infer
availability for one source family from another source family.

## PostgreSQL Readiness

On first run, the service must inspect PostgreSQL before source work begins.

The readiness check must verify:

- PostgreSQL can be reached with configured non-secret connection metadata.
- The expected schema exists or can be created safely.
- Required source-family tables exist or can be created safely.
- Required indexes and uniqueness constraints for idempotent insertion exist or
  can be created safely.
- Schema bootstrap is explicit in configuration and observable in run output.
- Schema bootstrap failures stop source execution and report a structured
  PostgreSQL readiness failure.

Table creation must be additive and safe. It must not drop tables, truncate
tables, delete records, rewrite existing source data, weaken constraints, or
silently migrate incompatible existing schemas.

## Year-State Contract

For each selected source family, the run must determine exactly one target year.

If PostgreSQL has no ingested data for the source family:

- `latest_year` is absent.
- `target_year` is the configured initial year.
- The default `target_year` is `2024` unless explicitly configured otherwise.
- The run status for year selection is `initial_year_selected`.

If PostgreSQL has ingested data for the source family:

- `latest_year` is the greatest year already committed for that source family.
- `target_year` is `latest_year + 1`.
- The run status for year selection is `next_year_selected`.

The run must not scan, download, backfill, or skip ahead to other years unless a
future task explicitly defines that behavior. This contract selects only the
initial year or the single next year.

## Discovery And Download Contract

Discovery and download are source-specific and target-year scoped.

For each selected source family:

- Discovery must be requested for `target_year` only.
- Download must be attempted only when discovery confirms an available source
  document for `target_year`.
- Downloaded source files must be archived with enough metadata to support
  replay and audit of the run.
- Discovery and download must produce structured status metadata without
  exposing credentials or secrets.

If a source owner has not published data for `target_year`, or the source is
temporarily unavailable in a way the source-specific adapter classifies as no
available year, the source-family result must be `no_available_source_year`.

`no_available_source_year` is a successful no-op for that source family. It must
not be treated as a failed production run unless every selected family is blocked
by an unrelated hard failure.

## Parse, Validate, And Insert Contract

When `target_year` source data exists:

- The archived source document is parsed by the source-family parser.
- Parsed records are validated before insertion.
- Validation failures are reported with structured counts and reasons.
- Accepted records are inserted into PostgreSQL in source-family tables.
- Insert results are reported with attempted, inserted, skipped, failed, and
  validation-failed counts.

Validation proves only that records satisfy the repository's explicit structural
and contract checks. It does not prove source-owner correctness, emission factor
correctness, unit conversion correctness, legal correctness, compliance
correctness, or carbon-accounting correctness.

## Idempotency Contract

Production inserts must be idempotent and safe on repeated execution.

For the same source family, source year, source document identity, and parsed
record identity, repeated execution must not create duplicate logical records.
The implementation must use reviewed PostgreSQL uniqueness constraints and a
documented conflict policy.

Repeated execution of a completed year must report deterministic duplicate or
already-ingested outcomes. It must not silently change existing records unless a
future reviewed task defines an explicit upsert or replacement policy.

If a prior run partially failed before commit, retry behavior must be governed by
the PostgreSQL transaction policy. A failed transaction must not leave ambiguous
partial ingestion state.

## No-Op Semantics

A source family no-ops when:

- PostgreSQL readiness succeeds.
- A target year is selected.
- Source-specific discovery determines that target-year data is not available.
- No download, parse, validation, or insert work is performed for that family.
- The family result is `no_available_source_year`.

A no-op must include:

- source family,
- latest ingested year, when present,
- target year,
- initial year configuration, when used,
- source discovery status,
- no-op reason,
- timestamp or run identifier, and
- zero attempted/inserted record counts.

The whole run may complete with a no-op result when all selected source families
report `no_available_source_year`.

## Docker PostgreSQL Integration Expectations

Integration tests for future implementation work must run against Docker
PostgreSQL on the user's Apple M3 development machine.

The expected integration test boundary is:

- Docker starts a PostgreSQL container for tests.
- Tests use an isolated database or schema per run.
- Tests create or verify required tables through the same bootstrap path used by
  the runtime.
- Tests cover first-run schema bootstrap.
- Tests cover no-existing-data initial year selection with default `2024`.
- Tests cover configured initial year override.
- Tests cover latest-year lookup and `next_year = latest_year + 1`.
- Tests cover `no_available_source_year` without failing the whole run.
- Tests cover idempotent repeated execution for already-ingested records.
- Tests cover transaction rollback or another reviewed no-partial-write policy.
- Tests must not call live endpoints.
- Tests must not require production credentials.

Default lightweight test runs may remain local-only, but implementation tasks
that claim production E2E ingestion behavior must include opt-in Docker
PostgreSQL integration validation.

## Required Observable Statuses

Future runtime results should expose stable statuses at the run and per-family
level.

Required per-family statuses:

- `postgresql_not_ready`
- `initial_year_selected`
- `next_year_selected`
- `source_year_available`
- `no_available_source_year`
- `downloaded`
- `archived`
- `parsed`
- `validated`
- `inserted`
- `completed`
- `completed_with_validation_failures`
- `failed`

The exact enum names may be refined by a future implementation task, but the
observable meanings must remain explicit.

## Non-Goals

This contract does not add or certify:

- Runtime source ingestion.
- Live endpoint calls.
- Database execution.
- Scheduler behavior.
- Parser correctness.
- Factor correctness.
- Source-owner correctness.
- Unit conversion correctness.
- Carbon-accounting correctness.
- Compliance or legal correctness.
- Production credentials.
- Backfill across multiple years.
- Multi-source-year catch-up in one family run.
- Destructive database migrations.

## Follow-Up Implementation Tasks

Future work should be split into focused tasks:

1. Define runtime configuration for selected source families, initial years,
   schema bootstrap mode, and PostgreSQL connection ownership.
2. Implement PostgreSQL schema bootstrap with additive table creation and
   integration tests.
3. Implement latest-ingested-year queries per source family.
4. Implement target-year planning using configured initial year or
   `latest_year + 1`.
5. Implement target-year-only discovery adapters for GHG Protocol, DEFRA/DESNZ,
   and IPCC EFDB without broad scans.
6. Implement target-year download and archive metadata.
7. Implement source-family parser and validation execution against archived
   documents.
8. Implement PostgreSQL idempotent insert behavior with reviewed uniqueness and
   conflict policy.
9. Implement structured run summaries and `no_available_source_year` no-op
   reporting.
10. Add Docker PostgreSQL integration tests for first run, next-year selection,
    no-op availability, idempotency, and rollback behavior on Apple M3.
11. Add operator runbook updates after implementation behavior exists.

## PR Footer Requirement

The pull request body for this task must end with:

```text
Task-ID: PH-010
Task-Issue: #576
```
