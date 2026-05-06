# PostgreSQL Execution Adapter Boundary

This document defines the PostgreSQL execution adapter boundary for future
runtime persistence work.

It is boundary documentation only. It does not add a PostgreSQL dependency,
import a database driver, open a database connection, run SQL, write records,
create tables, run migrations, load environment variables, load configuration
files, load credentials, perform HTTP or network calls, schedule work, or claim
production persistence readiness.

## Purpose

Future PostgreSQL runtime persistence will need an adapter that consumes
deterministic insert statement data and a caller-provided session contract. CO-102D
defines the handoff shape without implementing that adapter.

The current code boundary is:

- `PostgreSQLExecutionPlan`: metadata describing a future statement handoff.
- `PostgreSQLExecutionPlanResult`: structured plan-build status.
- `PostgreSQLExecutionResult`: disabled/no-execution result shape for future
  adapter reporting.
- `PostgreSQLExecutionAdapterProtocol`: protocol shape for future adapter
  metadata and plan-building behavior.
- `build_postgresql_execution_plan()`: pure helper that converts an existing
  `PostgreSQLInsertStatement` into plan metadata.
- `build_disabled_postgresql_execution_result()`: pure helper that reports
  runtime execution as disabled.
- `describe_postgresql_execution_adapter_boundary()`: side-effect-free boundary
  description.

## No-Execution Boundary

This boundary does not:

- Connect to PostgreSQL.
- Run SQL.
- Write records.
- Create tables.
- Run migrations.
- Start, commit, or roll back transactions.
- Import `psycopg`, SQLAlchemy, or `asyncpg`.
- Create a concrete runtime adapter.
- Change `PostgreSQLPersistenceRepository`.

`PostgreSQLExecutionStatus.READY` means an execution plan boundary was built
from statement metadata. It does not mean the statement was executed.

## Insert Builder Relationship

Future runtime execution must consume `build_postgresql_insert_statement()`
output. The execution adapter boundary must not duplicate SQL generation or
construct a second insert statement shape.

`build_postgresql_execution_plan()` preserves:

- SQL text.
- Ordered parameter rows.
- Target table name.
- Ordered column names.
- Record count.
- Idempotency key fields.
- Conflict target fields.

The plan wraps that data in `PostgreSQLStatementExecutionContract` so a future
runtime adapter can hand it to a caller-provided session after the safety gate is
satisfied.

## Connection Session Relationship

CO-102C introduced `PostgreSQLConnectionSession` and related caller-provided
session contract metadata. CO-102D consumes only the description and transaction
boundary metadata from that contract.

No session object is created in this task. No session method is called. Future
runtime adapters must still receive caller-provided session objects explicitly.

## Transaction Policy Relationship

`PostgreSQLTransactionPolicy` records the Phase 1 transaction policy for future
batch persistence. Execution plans may be wrapped in transaction policy metadata,
but this does not start, finish, or roll back a real transaction.

## Idempotency And Conflict Strategy Relationship

`PostgreSQLIdempotencyConflictStrategy` records the Phase 1 duplicate-handling
strategy for future batch persistence. Execution plans may carry idempotency and
conflict target metadata, but this does not change insert SQL or add conflict
SQL behavior.

## Repository Relationship

`PostgreSQLPersistenceRepository` remains a skeleton that returns unsupported
results. It must not call the execution adapter boundary as a runtime write path
until a future task explicitly satisfies the PostgreSQL implementation safety
gate.

The current boundary is safe for docs, previews, and future planning because it
only builds metadata and disabled results.

## Future Driver Relationship

CO-102B recommends a future synchronous `psycopg` 3 adapter direction. CO-102D
does not add that dependency and does not import any driver.

CO-102H adds a dedicated `psycopg` session adapter skeleton. It may preserve
execution plan metadata in disabled results, but it does not create connections,
create cursors, run SQL, write records, or make the repository executable.

A future adapter may map `PostgreSQLExecutionPlan` to the approved driver after:

- The driver dependency is added in a scoped task.
- A caller-provided session contract is implemented by a runtime object.
- Transaction behavior is approved.
- Integration tests are opt-in and isolated.
- The safety gate is satisfied.

## Status Semantics

- `ready`: future execution plan metadata was built; nothing ran.
- `disabled`: runtime execution is intentionally disabled.
- `unsupported`: a future adapter or caller may use this for unsupported
  capabilities.
- `failed`: plan construction or adapter-boundary validation failed.
- `no_statement`: no insert statement was available for plan construction.

## Related Documents

- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL psycopg Session Adapter Boundary](postgresql-psycopg-session-adapter-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
