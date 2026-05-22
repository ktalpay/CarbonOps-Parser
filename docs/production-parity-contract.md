# Production Parity Contract

This contract defines project-level production readiness for CarbonOps-Parser.
It is documentation only. It does not implement .NET runtime code, change
Python runtime behavior, add credentials, connect to PostgreSQL, download
sources, parse source files, write records, close issues, or claim that the
whole project is production-ready.

## Current Verdict

Project-level production-ready is blocked.

- Python runtime production path: yes, through the packaged
  `carbonops-parser run-ingestion` operator path.
- .NET runtime production path: no. The .NET runtime is not production-ready
  yet. The .NET tree now provides contracts, parity tests, a directly runnable
  scheduled-worker entrypoint baseline, and a production config
  loader/redaction baseline. It also has a .NET PostgreSQL schema
  bootstrap/year-state baseline for the shared/source-family runtime tables.
  Its ingestion command remains a safe not-yet-implemented placeholder.
- Project-level production-ready: no. The project cannot claim this until a
  user can choose either runtime and receive equivalent production behavior.

## Runtime Choice Requirement

A production-ready CarbonOps-Parser release must let an operator choose either
the Python runtime or the .NET runtime. Whichever runtime is selected, it must
be:

- Installable in an operator-owned environment.
- Configurable without committing secrets or raw connection strings.
- Runnable directly for a single ingestion cycle.
- Usable as a service or scheduled worker through documented operator steps.
- Stoppable and rerunnable without destructive cleanup.
- Troubleshootable from redacted structured diagnostics and documented failure
  modes.

The Python runtime currently has this documented operator path. The .NET runtime
has the scheduled-worker entrypoint shape plus real file/environment config
loading and redaction for `validate-config`, plus PostgreSQL schema
bootstrap/year-state runtime primitives; it does not yet provide equivalent
production ingestion behavior.

## Equivalent Data Contract

Python and .NET production runtimes must write equivalent parsed data into the
same PostgreSQL schema/model.

Equivalence requires:

- The same shared runtime tables and source-family year-state semantics.
- The same source-specific master/detail table families.
- The same PostgreSQL object names, required columns, constraints, indexes, and
  idempotency keys once the project-level schema is finalized.
- The same source family identifiers: `ghg_protocol`, `defra_desnz`, and
  `ipcc_efdb`.
- The same accepted, skipped, duplicate, validation-failed, conflict, and
  no-op count meanings.

Language-specific code structure may differ, but persisted PostgreSQL behavior
and operator-visible outcomes must not drift.

## Source Families

Both runtimes must support the same Phase 1 source families:

- GHG Protocol.
- DEFRA/DESNZ.
- IPCC EFDB.

Each runtime must discover, download or load, archive, parse, validate, and
persist the selected target year for each enabled source family through the same
production contract. A runtime is not production-parity complete if it supports
only a subset of these source families.

## Year Selection

For each enabled source family, both runtimes must select exactly one target
year per cycle.

Initial-year behavior:

- If PostgreSQL has no successful year-state data for the source family, select
  the configured initial year.
- The default initial year is `2024`.
- The effective initial year must be visible in configuration validation and run
  output.

Next-cycle behavior:

- If PostgreSQL contains successful imports for the source family, read the
  latest successful imported year from the database.
- Select `target_year = latest_successful_imported_year + 1`.
- Update year-state only after the source-family master/detail insert succeeds.

The runtimes must not silently backfill multiple years, skip ahead, or infer one
source family's target year from another family unless a future reviewed
contract explicitly changes that behavior.

## No Available Source Year

Both runtimes must implement the same `no_available_source_year` behavior.

When the target year has no available source data:

- The source-family result is a successful no-op, not a hard runtime failure.
- No source records are inserted.
- No latest-year state is advanced.
- The run output includes source family, latest year when present, target year,
  no-op reason, and zero attempted/inserted record counts.
- The whole run may complete when every selected source family reports
  `no_available_source_year`.

## Idempotency And Reruns

Both runtimes must provide equivalent idempotency and rerun behavior.

- Repeating a completed source-family year with the same source document and
  parsed record identities must not create duplicate logical records.
- Duplicate master/detail records must be reported as skipped or already
  ingested with deterministic counts.
- Same idempotency key with a different record checksum must be treated as a
  conflict unless a future reviewed replacement policy exists.
- Failed transactions must not leave ambiguous partial ingestion state.
- Rerunning after an operator-visible fix must use the same documented command
  shape and must not require destructive cleanup.

## Redaction And Secret Handling

Python and .NET runtimes must follow the same secret-handling contract.

- Runtime configuration must keep secrets outside committed files.
- PostgreSQL passwords, tokens, raw DSNs with credentials, private artifact URLs
  with credentials, and secret-store values must not be logged.
- Configuration validation and run summaries may report secret presence, but
  not secret values.
- Failure diagnostics, tickets, test output, and operator runbooks must use
  redacted examples.

## Operator Expectations

Both runtimes must document equivalent operator flows:

- Install.
- Configure.
- Validate configuration without opening PostgreSQL when possible.
- Validate PostgreSQL readiness in an isolated or approved target.
- Run one ingestion cycle directly.
- Schedule as a service or scheduled worker.
- Stop a running cycle without destructive cleanup.
- Rerun safely after fixes.
- Troubleshoot common configuration, PostgreSQL, source availability,
  validation, idempotency, and redaction failures.

The command names and service mechanisms may be runtime-specific, but the
operator-visible capabilities must be equivalent.

## Production Validation Expectations

Project-level production validation must include both runtime-specific evidence
and cross-runtime parity evidence:

- Python production operator validation.
- .NET production operator validation.
- PostgreSQL schema bootstrap validation for both runtimes.
- Initial-year `2024` validation for both runtimes.
- Latest-successful-year to next-year validation for both runtimes.
- `no_available_source_year` validation for both runtimes.
- Idempotent rerun validation for both runtimes.
- Redaction validation for both runtimes.
- Docker PostgreSQL end-to-end tests for the .NET runtime before it is marked
  production-ready.
- Python/.NET parity validation proving equivalent persisted rows, counts,
  statuses, and operator-visible behavior against the same schema.

## Follow-Up .NET Task Map

The implementation sequence for .NET production readiness is:

1. .NET service/scheduled-worker entrypoint. Satisfied by PROD-003 as an
   executable command-surface baseline only; ingestion parity remains incomplete.
2. .NET production config loader and redaction. Satisfied by PROD-004 for
   `validate-config` file/environment loading, deterministic environment
   override behavior, fail-closed diagnostics, and redaction only. Ingestion,
   PostgreSQL writes, and project-level production readiness remain incomplete.
3. .NET PostgreSQL schema bootstrap and year-state. Satisfied by PROD-005 for
   additive/idempotent DDL generation, explicit Npgsql runtime boundary,
   latest-successful-year lookup, next-year calculation, idempotent successful
   year-state recording, and redacted diagnostics only. .NET source
   discovery/download/parsing and source-specific master/detail inserts remain
   incomplete.
4. .NET source discovery/download/parsing orchestration.
5. .NET source-specific master/detail insert.
6. .NET idempotency and rerun behavior.
7. .NET Docker PostgreSQL E2E tests.
8. Python/.NET parity validation.
9. Final project production-ready verdict.

Each task must remain narrow, tested, and reviewable. None of these follow-up
tasks should be treated as complete merely because the Python runtime already
has an operator path.

## Blocking Rule

Project-level production-ready is blocked until both runtimes pass this
contract. Until then, documentation may claim only that the Python runtime has a
production operator path and that the .NET runtime remains non-production.
