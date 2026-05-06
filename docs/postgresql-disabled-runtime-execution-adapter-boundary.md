# PostgreSQL Disabled Runtime Execution Adapter Boundary

This document defines the disabled PostgreSQL runtime execution adapter boundary.

It is disabled/no-execution documentation only. It does not create a PostgreSQL
connection, create a cursor, run SQL, write records, start a transaction, finish
a transaction, roll back a transaction, create tables, run migrations, load
environment variables, load configuration files, load credentials, perform HTTP
or network calls, schedule work, or claim production persistence readiness.

## Purpose

CO-102I adds a disabled runtime adapter that composes existing PostgreSQL
runtime metadata into one structured no-execution result. It is useful for
future repository planning and tests because it shows what metadata a runtime
adapter would need without enabling database behavior.

The current code boundary is:

- `PostgreSQLDisabledRuntimeExecutionAdapter`: adapter object that builds
  disabled metadata only.
- `PostgreSQLDisabledRuntimeExecutionResult`: structured disabled result.
- `PostgreSQLDisabledRuntimeExecutionMetadata`: explicit no-execution markers.
- `build_postgresql_disabled_runtime_execution_result()`: helper that composes
  existing statement, execution-plan, transaction-policy, conflict-strategy, and
  optional session-adapter metadata.
- `describe_postgresql_disabled_runtime_execution()`: side-effect-free boundary
  description.

## Composed Metadata

The disabled adapter may preserve:

- Target table name.
- Record count.
- Statement count.
- SQL text as preview metadata.
- `PostgreSQLExecutionPlan` metadata.
- `PostgreSQLTransactionPolicy` and `PostgreSQLTransactionPlan` metadata.
- `PostgreSQLIdempotencyConflictStrategy` and conflict target metadata.
- Optional psycopg session adapter skeleton metadata supplied by the caller.
- Structured warning issues explaining runtime execution is disabled.

The adapter does not mutate SQL, add conflict SQL, change placeholder format, or
produce repository persistence semantics.

## No-Execution Markers

Every ready disabled result reports:

- `no_execution`: `True`
- `opens_connection`: `False`
- `creates_cursor`: `False`
- `runs_sql`: `False`
- `writes_records`: `False`
- `starts_transaction`: `False`
- `commits_transaction`: `False`
- `rolls_back_transaction`: `False`
- `creates_tables`: `False`
- `runs_migrations`: `False`
- `loads_environment`: `False`
- `loads_config_files`: `False`
- `loads_credentials`: `False`
- `runtime_enabled`: `False`

The result must not imply records were persisted, written, committed, rolled
back, skipped, upserted, or otherwise completed as a database operation.

## Relationship To Existing Boundaries

- CO-102D execution adapter boundary provides `PostgreSQLExecutionPlan`
  metadata.
- CO-102E transaction policy boundary provides single-batch policy metadata.
- CO-102F idempotency/conflict strategy boundary provides duplicate-handling
  strategy metadata without SQL mutation.
- CO-102H psycopg session adapter skeleton can supply optional disabled session
  metadata.
- `PostgreSQLPersistenceRepository` remains unsupported and must not call this
  boundary as a runtime write path.

## Future Use

A future repository execution task may use this disabled result shape as a
review reference after the PostgreSQL implementation safety gate is satisfied.
That future work must still add an explicit runtime adapter, caller-provided
session handling, transaction behavior, conflict behavior, opt-in integration
tests, and sanitized operational reporting in separately reviewed tasks.

## Related Documents

- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
- [PostgreSQL psycopg Session Adapter Boundary](postgresql-psycopg-session-adapter-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
