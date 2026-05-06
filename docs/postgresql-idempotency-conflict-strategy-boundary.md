# PostgreSQL Idempotency Conflict Strategy Boundary

This document defines the PostgreSQL idempotency and conflict strategy boundary
for future runtime persistence work.

It is strategy metadata only. It does not add a PostgreSQL dependency, import a
database driver, open a database connection, run SQL, write records, create
tables, run migrations, generate `ON CONFLICT` SQL, add `DO NOTHING`, add
`DO UPDATE`, load environment variables, load configuration files, load
credentials, perform HTTP or network calls, schedule work, or claim production
persistence readiness.

## Purpose

Future PostgreSQL runtime persistence needs explicit duplicate-handling behavior
before repository writes are enabled. CO-102F defines the Phase 1 strategy
metadata without changing SQL generation or runtime behavior.

The current code boundary is:

- `PostgreSQLIdempotencyConflictStrategy`: deterministic Phase 1 strategy
  metadata.
- `PostgreSQLConflictStrategyPlan`: metadata connecting an insert statement to
  the strategy.
- `PostgreSQLConflictStrategyPlanResult`: structured plan-build status.
- `build_default_postgresql_idempotency_conflict_strategy()`: returns the
  default Phase 1 strategy.
- `build_postgresql_conflict_strategy_plan()`: wraps an existing insert
  statement in strategy metadata.
- `describe_postgresql_idempotency_conflict_strategy_boundary()`:
  side-effect-free boundary description.

## Phase 1 Strategy

The default Phase 1 strategy is:

- Fail on conflict.
- Require existing idempotency metadata.
- No silent skip behavior.
- No upsert behavior.
- No SQL mutation.
- Runtime execution disabled.

This is strategy metadata only. It does not alter insert SQL, run SQL, or decide
real database conflict outcomes.

## Insert Builder Relationship

`build_postgresql_insert_statement()` already exposes:

- `idempotency_key_fields`
- `conflict_target_fields`

The strategy boundary consumes those fields as metadata. It must not duplicate
insert SQL generation and must not append PostgreSQL conflict clauses to the
statement text.

If idempotency or conflict target metadata is missing, the strategy plan returns
a structured failed result instead of producing a ready plan.

## Relationship To Other Boundaries

`PostgreSQLExecutionPlan` may preserve idempotency and conflict target metadata
for a future execution adapter, but it does not run SQL.

`PostgreSQLTransactionPolicy` may describe single-batch transaction metadata,
but it does not decide duplicate-handling runtime behavior by itself.

`PostgreSQLPersistenceRepository` remains a skeleton that returns unsupported
results. It must not use this strategy as a runtime write path until a future
task explicitly satisfies the PostgreSQL implementation safety gate.

## No-Execution Boundary

CO-102F does not add:

- PostgreSQL driver dependencies.
- Concrete runtime adapters.
- Database connections.
- SQL execution.
- Database writes.
- Conflict SQL generation.
- `DO NOTHING` behavior.
- `DO UPDATE` behavior.
- Migrations or table creation.
- Environment variable loading.
- Configuration file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler or background behavior.
- Production persistence readiness.

## Future Conflict Options

Future tasks may evaluate:

- Plain insert with duplicate-key errors mapped to structured issues.
- Explicit fail-on-conflict reporting with deterministic issue codes.
- `ON CONFLICT DO NOTHING` only after skipped-count reporting is approved.
- Upsert behavior only after overwrite, audit, and drift risks are reviewed.

Those options remain deferred. CO-102F does not implement them.

## Status Semantics

- `ready`: strategy metadata was built for an insert statement; nothing ran.
- `disabled`: runtime conflict handling is intentionally disabled.
- `unsupported`: a future adapter or caller may use this for unsupported
  conflict capabilities.
- `failed`: required idempotency or conflict metadata was missing.
- `no_statement`: no insert statement was available for strategy planning.

## Related Documents

- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
