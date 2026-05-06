# PostgreSQL Runtime Persistence Implementation Plan

This document plans a future PostgreSQL runtime persistence implementation.

It is planning documentation only. It does not connect to PostgreSQL, execute
SQL, write records, create tables, run migrations, load environment variables,
load configuration files, load credentials, perform HTTP or network calls,
schedule work, or claim production readiness.

## Current State

The current local flow can produce persistence-ready data without database
runtime behavior:

- Local fixture parsing can load already-acquired local content into parser input.
- The minimal DEFRA/DESNZ parser produces parser execution results and raw
  parsed payloads for fixture content only.
- Normalization input can be built from parser raw payloads.
- The minimal DEFRA/DESNZ normalization mapper can produce fixture-only
  normalized records.
- `PersistenceInput` can be built from successful normalization results.
- `build_postgresql_insert_statement()` can produce deterministic PostgreSQL
  insert statement data from `PersistenceInput`.
- `build_postgresql_persistence_preview()` can expose insert statement data as a
  preview-only result.
- `render_postgresql_ddl_preview()` can render review-only DDL text from the
  logical schema descriptor.
- `PostgreSQLPersistenceRepository` satisfies the repository protocol while
  returning unsupported results only.
- `pyproject.toml` declares the approved `psycopg` 3 dependency for future
  runtime adapter work, but pure persistence modules do not import it.
- The PostgreSQL implementation safety gate defines mandatory preconditions
  before any runtime database behavior may be added.
- `evaluate_postgresql_runtime_execution_gate()` records explicit future runtime
  execution intent as disabled/no-execution metadata.

## Explicit Non-Goals

CO-102A does not add:

- Runtime database writes.
- Runtime PostgreSQL driver imports or execution adapters.
- SQLAlchemy, `asyncpg`, or additional database dependencies.
- SQL execution.
- Migrations or table creation.
- Runtime repository behavior.
- Environment variable loading.
- Configuration file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.
- Production PostgreSQL persistence readiness.

`PostgreSQLPersistenceRepository` must remain unsupported and no-execution until
a later runtime task explicitly satisfies the safety gate.

## Future Implementation Sequence

Future runtime persistence should be split into small, reviewable tasks:

- CO-102B: choose PostgreSQL driver dependency and dependency boundary.
- CO-102C: define caller-provided connection or session contract.
- CO-102D: add repository execution adapter behind the explicit safety gate.
- CO-102E: define transaction boundary, rollback behavior, and result reporting.
- CO-102F: approve idempotency and conflict strategy.
- CO-102G: add the approved `psycopg` dependency boundary without execution.
- CO-102H: add opt-in PostgreSQL integration tests using the existing integration
  test boundary helper.
- CO-102I: add local PostgreSQL validation runbook and operator documentation.

Each task should have its own branch, focused tests, safety review, and explicit
confirmation that the safety gate still blocks unintended writes.

## Dependency Strategy

Candidate directions:

- `psycopg`: practical Phase 1 direction for a synchronous Python CLI/service
  path. It has direct PostgreSQL semantics, parameterized execution support, and
  a smaller conceptual footprint than a full ORM.
- SQLAlchemy: useful when object mapping, dialect abstraction, or cross-database
  query composition is needed. It is heavier than the current boundary requires
  and could obscure the existing insert builder contract.
- `asyncpg`: useful for async services with event-loop ownership. It would add
  async boundary decisions before the project has a runtime repository path.

Recommendation for Phase 1: plan toward a narrow synchronous `psycopg` adapter
behind an explicit dependency boundary. CO-102G adds the dependency declaration
only; the runtime adapter remains deferred. This keeps the first runtime
implementation close to the existing parameterized insert builder and local
CLI/service usage.

The [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
records the focused Phase 1 driver decision. It recommends a future synchronous
`psycopg` 3 adapter and records that CO-102G adds the dependency without
execution behavior.

## Connection And Config Strategy

Runtime persistence should use caller-provided values only. Library code should
not implicitly load environment variables, config files, or credentials.

The existing `PostgreSQLPersistenceOptions` contract can remain the pure library
shape for connection-shaped metadata. A future application or CLI layer may own
configuration loading, but that loading must stay outside the core repository
boundary and must be explicitly opted in.

The [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
defines the driver-neutral shape for future caller-provided session objects. It
does not create a real connection/session, import a database driver, or enable
runtime SQL execution.

Secrets must not appear in docs, fixtures, exceptions, logs, or repository
metadata. Future config work should continue using redacted markers, such as a
password-present flag, rather than storing secret values in public contracts.

## Execution Boundary

The runtime repository should consume output from
`build_postgresql_insert_statement()`. It should not duplicate SQL generation or
construct a second insert statement shape.

The [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
defines the no-execution handoff shape between insert-builder output and a
future caller-provided session. It builds plan metadata only; it does not create
a connection, run SQL, or change repository behavior.

The execution layer should be replaceable and testable:

- A small executor/session adapter can own the actual database call.
- The repository can translate `PersistenceInput` into insert builder output.
- The executor can receive SQL text and ordered parameter rows.
- Tests can use fake executors for repository behavior without a database.

Repository execution must not happen silently. A future runtime repository should
require an explicit configured repository instance or explicit execution adapter
and should keep the current unsupported behavior as the default no-execution
state.

The [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
adds the explicit enablement gate for that future work. It is disabled by
default, remains metadata-only, and does not enable repository execution.

The [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
defines the go/no-go criteria that must be satisfied before the first real
runtime execution task begins.

## Transaction Strategy

The first runtime implementation should use one transaction per
`PersistenceInput` batch. All rows in that batch should succeed or the batch
should roll back.

The [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
records this Phase 1 transaction policy as metadata only. It does not start,
finish, or roll back a real transaction.

Recommended initial policy:

- Begin a transaction for one ready `PersistenceInput`.
- Execute the prepared insert statement with ordered parameter rows.
- Commit only after the full batch succeeds.
- Roll back on any execution failure.
- Report attempted record count, persisted record count, and structured issues
  deterministically.

Partial success should not be reported for the first implementation unless a
later task explicitly introduces chunking. If chunking is added later, the result
contract must distinguish attempted, persisted, skipped, and failed counts.

## Idempotency And Conflict Strategy

The logical schema descriptor and insert builder already expose idempotency key
metadata. Future runtime persistence should use that metadata as input to the
approved conflict policy.

The [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
records the Phase 1 fail-on-conflict strategy as metadata only. It does not
change insert SQL, generate conflict SQL, run SQL, or write records.

Options:

- Plain insert: simplest and safest for surfacing duplicate-key failures early.
  It is noisy but makes idempotency issues visible.
- `ON CONFLICT DO NOTHING`: useful for idempotent replays, but it can hide
  unexpected source or normalization drift unless skipped counts are reported.
- Explicit fail-on-conflict: similar to plain insert, but the repository can map
  conflict errors into clearer structured issues.

Recommended first path: start with plain insert or explicit fail-on-conflict,
then add `ON CONFLICT DO NOTHING` only after skipped-count reporting and
operator expectations are documented. Do not implement conflict SQL in CO-102A.

## Schema And Table Lifecycle Strategy

`PostgreSQLPersistenceSchema` is logical metadata. `render_postgresql_ddl_preview()`
is review text only. Neither should create tables or run migrations.

Safest Phase 1 production path:

- Require tables to be created by a separate migration process before repository
  writes are enabled.
- Keep DDL preview as documentation/review input, not an execution path.
- Do not hide table creation inside repository construction or `persist()`.

Explicit opt-in table creation should remain deferred until migration ownership,
rollback behavior, and operational controls are approved.

## Integration Test Strategy

Future integration tests should use the existing PostgreSQL integration test
boundary helper and remain disabled by default.

Rules for the first runtime write task:

- Tests require explicit opt-in.
- Tests target an isolated test database only.
- No credentials or DSNs are committed.
- Normal test runs do not import a database dependency unless the optional test
  path is explicitly enabled.
- Tests verify success, duplicate/conflict behavior, rollback, no-record input,
  unsupported/not-enabled behavior, and sanitized errors.

## Observability And Safety

Runtime repository results should report:

- Status.
- Attempted record count.
- Persisted record count.
- Structured issues.
- Sanitized repository metadata.

Errors must be sanitized. SQL parameter values should not be logged in unsafe
contexts. Secret values must never appear in exceptions, logs, docs, fixtures, or
test output.

The default behavior should remain unsupported or not-enabled until a caller
explicitly constructs a runtime-capable repository with approved configuration.

## Acceptance Criteria For First Runtime Persistence Task

The first task that adds runtime PostgreSQL persistence must pass this checklist:

- The PostgreSQL implementation safety gate is explicitly satisfied.
- The PostgreSQL runtime readiness checklist has a go decision.
- The `psycopg` dependency remains isolated from pure preview/domain modules.
- Runtime writes require explicit caller-provided configuration.
- No default local, staging, production, or cloud database target exists.
- SQL generation delegates to `build_postgresql_insert_statement()`.
- Repository execution is testable with a fake executor/session.
- Integration tests are opt-in and disabled by default.
- Test database setup is documented and isolated.
- Transaction, rollback, and conflict behavior are documented and tested.
- `PersistenceResult` reports attempted and persisted counts deterministically.
- Errors are sanitized and do not expose secrets or unsafe parameter values.
- Documentation states that production hardening remains separate unless it has
  been explicitly completed.
- `python -m pytest`, public safety checks, and whitespace checks pass.

## Risks And Mitigations

- Schema drift: keep logical schema descriptors, migration DDL, and insert
  columns reviewed together.
- Duplicate records: start with visible conflict behavior before silent skipping.
- Partial writes: use single-batch rollback for the first implementation.
- Credential leaks: keep secret loading outside public contracts and redact all
  operational metadata.
- Production misuse: require explicit configuration and no default database
  target.
- Dependency footprint: choose the narrowest driver boundary needed for Phase 1.
- SQL compatibility: keep generated SQL deterministic and covered by tests
  before executing it.

## Related Documents

- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [Public Safety](public-safety.md)
