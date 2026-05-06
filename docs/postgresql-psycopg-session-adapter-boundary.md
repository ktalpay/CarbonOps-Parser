# PostgreSQL psycopg Session Adapter Boundary

This document defines the `psycopg`-specific PostgreSQL session adapter skeleton
boundary for future runtime persistence work.

It is skeleton documentation only. It does not create a PostgreSQL connection,
create a cursor, run SQL, write records, start a transaction, finish a
transaction, roll back a transaction, create tables, run migrations, load
environment variables, load configuration files, load credentials, perform HTTP
or network calls, schedule work, or claim production persistence readiness.

## Purpose

CO-102H adds a dedicated `psycopg` adapter skeleton after the approved
dependency boundary from CO-102G. The skeleton exists to make the future runtime
adapter boundary explicit while keeping all current behavior disabled.

The current code boundary is:

- `PsycopgPostgreSQLSessionAdapter`: metadata-only wrapper for a future
  caller-provided `psycopg` session or connection object.
- `PsycopgPostgreSQLSessionAdapterMetadata`: deterministic capability metadata.
- `PsycopgPostgreSQLSessionAdapterBoundaryResult`: structured disabled
  boundary result.
- `build_psycopg_session_adapter_metadata()`: side-effect-free metadata helper.
- `validate_psycopg_session_adapter_boundary()`: no-execution boundary check.

## Import Boundary

The `psycopg` import is limited to the dedicated adapter skeleton module and
focused tests. Pure persistence modules remain driver-free:

- PostgreSQL logical schema descriptor.
- PostgreSQL DDL preview renderer.
- PostgreSQL insert SQL builder.
- PostgreSQL persistence preview.
- PostgreSQL connection/session contract.
- PostgreSQL execution adapter boundary.
- PostgreSQL transaction policy.
- PostgreSQL idempotency/conflict strategy.
- Local dry-run CLI and pipeline code.
- `PostgreSQLPersistenceRepository` skeleton.

The adapter skeleton does not import SQLAlchemy or `asyncpg`.

## Caller-Provided Session Strategy

The skeleton may receive a caller-provided session reference, but it must not use
that reference for runtime behavior in this task. It does not inspect the
session object, create a connection, create a cursor, run statements, start
transactions, finish transactions, or roll back transactions.

Future runtime work may map a caller-provided `psycopg` session to the
driver-neutral `PostgreSQLConnectionSession` contract only after an explicit
safety-gated task.

## Disabled Behavior

The adapter skeleton reports disabled/no-execution metadata:

- `runtime_enabled`: `False`
- `opens_connection`: `False`
- `creates_cursor`: `False`
- `runs_sql`: `False`
- `writes_records`: `False`
- `starts_transaction`: `False`
- `commits_transaction`: `False`
- `rolls_back_transaction`: `False`
- `loads_environment`: `False`
- `loads_config_files`: `False`
- `loads_credentials`: `False`

Disabled execution result helpers may preserve `PostgreSQLExecutionPlan`
metadata, such as statement count and target table, but they do not run the
statement and must not imply persisted records.

## Relationship To Existing Boundaries

- CO-102B selected a future synchronous `psycopg` direction.
- CO-102C defines the driver-neutral caller-provided session contract.
- CO-102D defines the no-execution execution adapter plan/result boundary.
- CO-102E defines future transaction policy metadata only.
- CO-102F defines future idempotency/conflict strategy metadata only.
- CO-102G adds the `psycopg` dependency declaration without runtime behavior.

CO-102H adds only the dedicated adapter skeleton. It does not convert
`PostgreSQLPersistenceRepository` into an executing repository and does not wire
the local dry-run preview path to runtime persistence.

CO-102I may accept psycopg session adapter skeleton metadata as optional disabled
runtime metadata. That disabled runtime adapter does not import psycopg, create
connections or cursors, run SQL, or turn the repository into a write path.

## Future Use

A future runtime adapter task may add concrete `psycopg` behavior only after the
PostgreSQL implementation safety gate is satisfied. That future task should:

- Accept caller-provided sessions explicitly.
- Keep environment, configuration, and credential loading outside pure library
  modules.
- Consume existing insert-builder and execution-plan output.
- Preserve import-boundary tests so preview modules stay driver-free.
- Add fake-session unit tests before opt-in PostgreSQL integration tests.
- Keep runtime repository behavior explicit and review-gated.

## Related Documents

- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
- [PostgreSQL Disabled Runtime Execution Adapter Boundary](postgresql-disabled-runtime-execution-adapter-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
