# PostgreSQL Driver Dependency Decision

This document records the PostgreSQL driver dependency decision for future
runtime persistence work.

It is decision documentation only. It does not add a database dependency, import
a database driver, connect to PostgreSQL, execute SQL, write records, create
tables, run migrations, load environment variables, load configuration files,
load credentials, perform HTTP or network calls, schedule work, or claim
production persistence readiness.

## Decision Summary

Recommended Phase 1 direction: use a narrow synchronous `psycopg` 3 runtime
adapter when PostgreSQL execution is later approved.

No dependency is added in CO-102B. `psycopg`, SQLAlchemy, and `asyncpg` remain
absent from project dependency files and runtime imports until a later scoped
dependency-boundary task.

## Evaluation Options

### psycopg 3

`psycopg` 3 is a direct PostgreSQL driver. It supports parameterized SQL,
explicit transaction control, synchronous usage, and optional async APIs if the
project later needs them.

For this project, its strongest fit is a small synchronous execution adapter
that consumes the existing insert SQL builder output without introducing ORM
concepts.

### SQLAlchemy Core / Engine

SQLAlchemy Core and Engine provide a broad database abstraction, connection
pooling patterns, dialect handling, and SQL expression construction.

Those capabilities may become useful later, but Phase 1 already has a
deterministic insert SQL builder. Introducing SQLAlchemy now would add a larger
dependency and a second SQL construction abstraction before the repository has a
runtime execution boundary.

### asyncpg

`asyncpg` is a PostgreSQL driver optimized for asynchronous applications. It can
be a strong fit for event-loop-owned services and high-throughput async
workloads.

The current local CLI and planned first repository path are synchronous. Choosing
`asyncpg` first would force async boundary, test harness, and caller lifecycle
decisions before runtime persistence exists.

## Evaluation Criteria

The Phase 1 driver direction is evaluated against:

- Minimal dependency footprint.
- Synchronous CLI/service suitability.
- Explicit transaction control.
- Parameterized SQL support.
- Compatibility with existing SQL builder output.
- Testability with caller-provided connection or session boundaries.
- Operational simplicity.
- Avoiding unnecessary ORM or SQL abstraction for Phase 1.
- Future extensibility.

## Recommendation

Use `psycopg` 3 as the preferred Phase 1 PostgreSQL driver direction, introduced
later in a dedicated dependency-boundary task.

The initial runtime design should be synchronous, direct-driver based, and
without an ORM. The future execution adapter should consume
`build_postgresql_insert_statement()` output and should avoid duplicating SQL
generation.

This recommendation does not approve runtime persistence by itself. Runtime
execution still requires the PostgreSQL implementation safety gate, an explicit
connection/session contract, opt-in integration tests, transaction policy, and
credential/config ownership decisions.

## Non-Goals

CO-102B does not add:

- PostgreSQL dependency installation.
- Runtime execution.
- Connection or session implementation.
- SQL execution.
- Schema creation or migrations.
- Credential loading.
- Configuration loading.
- Environment variable loading.
- Runtime repository behavior.
- Production persistence readiness.

## Future Dependency Boundary

The future dependency should be introduced in a small dedicated task, such as
CO-102C or a follow-up dependency-boundary task if sequencing changes.

That task should:

- Add the dependency explicitly.
- Explain why the dependency is needed at that point.
- Keep pure domain, preview, schema, and SQL-builder modules driver-free.
- Add focused tests for import boundaries.
- Keep `PostgreSQLPersistenceRepository` no-execution unless runtime execution
  is explicitly in scope.
- Avoid changing PostgreSQL persistence preview behavior.
- Avoid importing the driver in pure preview modules.
- Update public safety checks if needed.
- Keep credential/config loading out of the dependency task.

## Import Boundary Strategy

Pure modules must remain driver-free:

- `persistence.input`
- `persistence.schema`
- `persistence.ddl_preview`
- `persistence.postgresql_insert_builder`
- `persistence.postgresql_persistence_preview`
- parser, normalization, and local dry-run pipeline modules

Future driver imports should live only in runtime execution adapter modules.
Tests should protect that preview modules and pure contracts do not import
PostgreSQL drivers or ORM packages.

## Parameter Style Compatibility

The existing insert SQL builder emits deterministic `%s` placeholders and ordered
parameter rows.

Before runtime execution is added, the selected driver task must verify
placeholder compatibility with the driver execution API. If the future adapter
needs a different placeholder style or parameter shape, it should introduce a
small runtime mapping layer inside the execution adapter.

The SQL builder should not be changed in CO-102B. Preview output should remain
stable and no-execution.

## Transaction And Session Implications

CO-102C should define the caller-provided connection or session contract. The
driver direction should support:

- Explicit transaction start/commit/rollback behavior.
- Caller ownership of connection/session lifecycle.
- Fake session or executor tests without a real database.
- No implicit connection creation in library code.

The repository must not construct a database connection from environment
variables, config files, or credentials on its own.

## Risk Analysis

- Dependency footprint: even a direct driver increases install surface. Mitigate
  by adding it only when runtime execution is scoped.
- Driver-specific placeholder semantics: `%s` compatibility must be verified
  before execution. Mitigate with adapter-level tests.
- ORM migration pressure: SQLAlchemy may be tempting later. Mitigate by keeping
  Phase 1 direct and measuring actual abstraction needs.
- Async complexity: async-first choices affect callers and tests. Mitigate by
  starting synchronous for the CLI/service path.
- Driver details leaking into pure modules: mitigate with import-boundary tests.
- Credential/config misuse: keep config loading outside core library modules and
  redact secrets by default.
- Test environment fragility: use default-disabled, explicit opt-in integration
  tests against an isolated test database only.

## Acceptance Criteria For Future Dependency-Add Task

A future task that adds the PostgreSQL driver dependency should pass this
checklist:

- The dependency is added explicitly and only in the scoped task.
- No runtime SQL execution is added unless that task explicitly includes it.
- Pure domain, preview, schema, and insert-builder modules remain driver-free.
- Tests verify import boundaries.
- Public safety checks are updated if needed.
- Documentation explains the dependency and its boundaries.
- No credentials, DSNs, or config loading are added.
- Normal test runs do not connect to PostgreSQL.
- `PostgreSQLPersistenceRepository` remains unsupported unless runtime execution
  is explicitly scoped and safety-gated.

## Related Documents

- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [Public Safety](public-safety.md)
