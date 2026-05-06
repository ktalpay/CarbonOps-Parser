# PostgreSQL Transaction Policy Boundary

This document defines the PostgreSQL transaction policy boundary for future
runtime persistence work.

It is policy documentation only. It does not add a PostgreSQL dependency, import
a database driver, open a database connection, run SQL, write records, create
tables, run migrations, start a real transaction, commit a real transaction,
roll back a real transaction, load environment variables, load configuration
files, load credentials, perform HTTP or network calls, schedule work, or claim
production persistence readiness.

## Purpose

Future PostgreSQL runtime persistence needs an explicit transaction policy before
any repository can write records. CO-102E defines the Phase 1 policy metadata
without implementing transaction behavior.

The current code boundary is:

- `PostgreSQLTransactionPolicy`: deterministic Phase 1 policy metadata.
- `PostgreSQLTransactionPlan`: metadata connecting an execution plan to the
  transaction policy.
- `PostgreSQLTransactionPlanResult`: structured plan-build status.
- `build_default_postgresql_transaction_policy()`: returns the default Phase 1
  policy.
- `build_postgresql_transaction_plan()`: wraps a no-execution execution plan in
  policy metadata.
- `describe_postgresql_transaction_policy_boundary()`: side-effect-free boundary
  description.

## Phase 1 Policy

The default Phase 1 policy is:

- Single batch transaction policy.
- Caller-provided session required.
- Caller-owned transaction boundary.
- No partial success for Phase 1.
- Future full-batch rollback-on-failure policy.
- Deterministic failure reporting.
- Runtime execution disabled.

This is policy metadata only. It does not start, finish, or roll back a real
transaction.

## Relationship To Existing Boundaries

`PostgreSQLConnectionSession` defines the future caller-provided session shape.
The transaction policy requires that caller-provided session boundary, but it
does not create a session or call a session method.

`PostgreSQLExecutionPlan` defines the future statement handoff metadata. The
transaction plan consumes that metadata and preserves record and statement
counts. It does not run SQL.

`PostgreSQLPersistenceRepository` remains a skeleton that returns unsupported
results. It must not use this policy as a runtime write path until a future task
explicitly satisfies the PostgreSQL implementation safety gate.

## No-Execution Boundary

CO-102E does not add:

- PostgreSQL driver dependencies.
- Concrete runtime adapters.
- Database connections.
- SQL execution.
- Database writes.
- Real transaction start behavior.
- Real transaction completion behavior.
- Real transaction rollback behavior.
- Migrations or table creation.
- Environment variable loading.
- Configuration file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler or background behavior.
- Production persistence readiness.

## Future Driver Relationship

CO-102B recommends a future synchronous `psycopg` 3 adapter direction. CO-102E
does not add that dependency and does not import any driver.

A future runtime adapter may use this policy only after:

- The driver dependency is added in a scoped task.
- A caller-provided session object exists.
- Transaction behavior is implemented behind the safety gate.
- Opt-in integration tests cover success and failure behavior.
- Operational logging and sanitized error handling are documented.

## Status Semantics

- `ready`: policy metadata was built for a future execution plan; nothing ran.
- `disabled`: runtime transaction behavior is intentionally disabled.
- `unsupported`: a future adapter or caller may use this for unsupported
  transaction capabilities.
- `failed`: policy plan construction failed.
- `no_statement`: no execution plan was available for policy planning.

## Related Documents

- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
