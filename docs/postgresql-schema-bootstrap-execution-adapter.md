# PostgreSQL Schema Bootstrap Execution Adapter Boundary

This document defines the future PostgreSQL schema bootstrap execution adapter
boundary for CarbonOps-Parser.

It is boundary documentation only. It does not add runtime code, create a
PostgreSQL connection, create a cursor, execute SQL, create tables, create
indexes, run migrations, load environment variables, load configuration files,
load credentials, perform network calls, modify product runtime behavior, or
claim production persistence readiness.

## Purpose

DB-042 defines how future schema bootstrap execution should bridge rendered
schema bootstrap SQL plans to an execution boundary. The boundary is deliberately
runtime-passive in this task: it describes the handoff shape, safety gates, and
review constraints without making the repository executable.

The future adapter may consume metadata from
`build_postgresql_phase1_schema_bootstrap_plan()`, including:

- target database engine.
- schema phase marker.
- required table names.
- ordered `CREATE TABLE` statement metadata.
- ordered `CREATE INDEX` statement metadata.
- no-execution markers from the bootstrap plan.

The future adapter must treat rendered SQL as plan data until a later task
explicitly enables execution behind the PostgreSQL safety gates.

## Adapter Boundary

A future schema bootstrap execution adapter should own only the narrow bridge
between a rendered bootstrap plan and a caller-provided execution/session
boundary.

The adapter boundary may be responsible for:

- validating that the incoming bootstrap plan targets PostgreSQL.
- preserving deterministic statement order from the rendered plan.
- separating table-creation statements from index-creation statements for
  diagnostics.
- reporting attempted statement counts without implying execution.
- forwarding sanitized execution results from a future caller-provided session.
- returning disabled, blocked, or failed-closed results when execution is not
  explicitly allowed.

The adapter boundary must not be responsible for:

- rendering DDL from schema catalog metadata.
- discovering database connection settings.
- creating implicit sessions or connections.
- loading credentials.
- deciding production or staging targets.
- running migrations.
- seeding data.
- modifying parser, downloader, scheduler, or persistence runtime behavior.

## Future Handoff Sequence

A future runtime-capable bootstrap flow should follow this order:

1. Build a deterministic schema bootstrap plan from the schema catalog and DDL
   renderer.
2. Evaluate the runtime execution gate and schema bootstrap opt-in controls.
3. Reject missing, ambiguous, production, staging, or shared database targets
   before any connection or SQL execution is possible.
4. Require a caller-provided, test-isolated session boundary.
5. Hand ordered bootstrap statements to the execution adapter only after all
   safety gates pass.
6. Execute through the caller-provided session boundary in a future task that
   explicitly permits SQL execution.
7. Return sanitized statement-level status metadata without logging credentials
   or raw connection strings.

DB-042 completes step-boundary documentation only. It does not implement steps
2 through 7.

## Fail-Closed Requirements

Until a later task explicitly enables schema bootstrap execution, the adapter
boundary must fail closed:

- default behavior is disabled/no-execution.
- absent opt-in means no connection and no SQL execution.
- incomplete safety-gate metadata means blocked/no-execution.
- missing caller-provided session means blocked/no-execution.
- production, staging, shared development, unlabeled, or implicit default
  database targets must be rejected before execution.
- invalid or non-PostgreSQL provider metadata must be rejected before execution.
- result metadata must not imply that tables or indexes were created when SQL
  did not run.

`CREATE_MISSING` intent in bootstrap metadata is not enough by itself to execute
DDL. It must be paired with explicit runtime enablement, a safe test-isolated
target, caller-provided session ownership, and a future task that permits SQL
execution.

## Test Isolation Requirements

Future tests for this adapter must be opt-in and isolated from the default test
suite. They must not run during default `python -m pytest`.

Future execution tests must use a disposable PostgreSQL target owned by the test
run, such as an explicitly opted-in local or CI service container. Tests must
not connect to production, staging, shared development, customer, or private
source databases.

The adapter contract should remain testable without PostgreSQL by using
metadata-only disabled or fake-session results. Real PostgreSQL execution tests
must remain separately marked, explicitly opted in, and scoped to a disposable
database.

## Relationship To Existing Boundaries

`build_postgresql_phase1_schema_bootstrap_plan()` remains the deterministic
planner that renders SQL metadata. It does not execute SQL and does not become
an adapter.

`render_postgresql_phase1_schema_ddl()` remains a DDL rendering helper. It must
not open connections, execute SQL, or create tables.

The PostgreSQL runtime execution gate remains disabled by default. Schema
bootstrap execution must not bypass it.

The PostgreSQL implementation safety gate remains the mandatory review boundary
before any runtime PostgreSQL connection, SQL execution, migration, table
creation, or schema bootstrap behavior is added.

The integration test container strategy defines the future safe target shape
for opt-in tests. Container strategy alone does not enable SQL execution.

## Non-Goals

DB-042 does not add:

- source code.
- migrations.
- runtime database connections.
- SQL execution.
- schema creation.
- index creation.
- production or staging configuration.
- credentials or secrets.
- environment/config loading.
- repository runtime behavior.
- downloader, parser, scheduler, or persistence coupling.

## Related Documents

- [PostgreSQL Bootstrap Boundary Contract (Phase 1)](postgresql-bootstrap-boundary.md)
- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
- [PostgreSQL DDL Strategy Contract (Phase 1 Planning)](postgresql-ddl-strategy-contract.md)
- [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Integration Test Container Strategy](postgresql-integration-test-container-strategy.md)
- [PostgreSQL Runtime Integration Boundary](postgresql-runtime-integration-boundary.md)
