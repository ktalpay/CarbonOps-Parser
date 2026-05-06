# PostgreSQL Connection Session Contract Boundary

This document defines the caller-provided PostgreSQL connection/session contract
boundary for future runtime persistence work.

It is contract documentation only. It does not import a database driver, open a
database connection, run SQL, write records, create tables, run migrations, load
environment variables, load configuration files, load credentials, perform HTTP
or network calls, schedule work, or claim production persistence readiness.

## Purpose

Future PostgreSQL runtime persistence needs a narrow way for repository code to
receive a caller-provided session-like object. CO-102C defines that shape without
creating a real connection/session and without importing a driver.

The current code boundary is:

- `PostgreSQLConnectionSession`: driver-neutral protocol for future
  caller-provided session objects.
- `PostgreSQLStatementExecutionContract`: parameterized statement handoff shape
  for a future runtime adapter.
- `PostgreSQLTransactionBoundary`: descriptive transaction ownership and mode
  metadata.
- `describe_postgresql_connection_session_contract()`: side-effect-free helper
  that reports the boundary assumptions.

## Caller-Provided Strategy

Library code must not implicitly load environment variables, config files, or
credentials to construct a database session. A future application or CLI layer
may own explicit configuration, but the pure persistence package should receive
already-constructed caller-provided runtime objects.

This keeps the persistence repository boundary reviewable:

- Configuration ownership stays outside pure library modules.
- Secret loading stays outside public contracts and docs.
- Tests can use fake sessions without a database.
- Runtime-capable adapters can remain behind the PostgreSQL implementation
  safety gate.

## Driver Neutrality

The contract is deliberately driver-neutral:

- No `psycopg` import.
- No SQLAlchemy import.
- No `asyncpg` import.
- No concrete driver class dependency.
- No database dependency is imported or used by this contract.

CO-102B recommends a future synchronous `psycopg` 3 direction, and CO-102G adds
the dependency declaration. This contract still does not import or require that
driver at runtime. A future adapter can map the protocol to the approved driver
after execution is explicitly scoped.

CO-102H adds a dedicated `psycopg` session adapter skeleton. That skeleton keeps
`psycopg` references isolated to the runtime adapter boundary and focused tests,
does not create connections or run SQL, and does not change this driver-neutral
contract.

## Statement Handoff Shape

`PostgreSQLStatementExecutionContract` carries:

- SQL text from the existing insert SQL builder.
- Ordered or named parameter data.
- Optional statement metadata.

The contract does not run the SQL text. Future repository execution should
consume output from `build_postgresql_insert_statement()` and wrap it in this
handoff shape without duplicating SQL generation.

## Transaction Boundary

`PostgreSQLTransactionBoundary` records descriptive future policy:

- Transaction ownership: caller-owned by default, repository-owned only in a
  future scoped task.
- Transaction mode: caller-managed by default, single-batch behavior only in a
  future scoped task.
- Rollback-on-failure marker: descriptive only in this task.

CO-102C does not start, finish, or roll back transactions. Runtime transaction
behavior remains deferred to a later safety-gated implementation task.

## Relationship To Existing Boundaries

- `PostgreSQLPersistenceOptions` remains a caller-provided config-shaped value
  contract and does not create sessions.
- `build_postgresql_insert_statement()` remains deterministic SQL statement data
  construction only.
- `PostgreSQLExecutionPlan` may wrap insert-builder output and session boundary
  metadata for a future runtime adapter, but it does not call a session or run
  SQL.
- `PostgreSQLTransactionPolicy` may describe future single-batch transaction
  policy, but it does not start, finish, or roll back a real transaction.
- `build_postgresql_persistence_preview()` remains preview-only and must stay
  driver-free.
- `PostgreSQLPersistenceRepository` remains a skeleton that returns unsupported
  results and does not use this session contract for runtime behavior yet.

## Out Of Scope

CO-102C does not add:

- PostgreSQL driver imports.
- Concrete psycopg adapter behavior.
- Runtime database connections.
- SQL execution.
- Database writes.
- Migrations or table creation.
- Environment variable loading.
- Configuration file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler or background behavior.
- Production persistence readiness.

## Future Use

A future runtime repository task may use this contract after the safety gate is
satisfied. That future task should:

- Use the approved driver dependency only inside runtime adapter modules.
- Keep pure preview modules driver-free.
- Accept caller-provided session objects.
- Consume insert-builder output instead of building SQL again.
- Add fake-session unit tests before opt-in database integration tests.
- Preserve sanitized error and result reporting.

## Related Documents

- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL psycopg Session Adapter Boundary](postgresql-psycopg-session-adapter-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
