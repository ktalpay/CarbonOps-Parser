# PostgreSQL Repository Disabled Execution Preview Boundary

This document defines the repository-level disabled execution preview boundary.

It is preview and diagnostic documentation only. It does not create a
PostgreSQL connection, create a cursor, run SQL, write records, start a
transaction, finish a transaction, roll back a transaction, create tables, run
migrations, load environment variables, load configuration files, load
credentials, perform HTTP or network calls, schedule work, or claim production
persistence readiness.

## Purpose

CO-102J adds a repository-adjacent helper that accepts `PersistenceInput` and
builds disabled PostgreSQL runtime execution metadata for diagnostics. It shows
how repository-level inputs can be composed into the existing no-execution
runtime result without changing repository persistence behavior.

The boundary is deliberately separate from `PostgreSQLPersistenceRepository`
execution semantics. `PostgreSQLPersistenceRepository.persist()` continues to
return unsupported/no-execution results and must not call this helper as a
runtime write path.

CO-102K adds a runtime execution gate that remains disabled by default. Future
repository execution work must use an explicit gate decision before runtime
behavior is considered; this preview helper still returns diagnostics only.

The runtime readiness checklist must have a go decision before any future task
converts repository diagnostics into real runtime execution behavior.

The current code boundary is:

- `build_postgresql_repository_disabled_execution_preview()`: accepts
  `PersistenceInput` and returns repository-level disabled preview metadata.
- `PostgreSQLRepositoryDisabledExecutionPreviewResult`: structured diagnostic
  result for repository-adjacent preview data.
- `PostgreSQLRepositoryDisabledExecutionPreviewStatus`: disabled, no-records,
  failed, and unsupported preview statuses.
- `describe_postgresql_repository_disabled_execution_preview()`: side-effect
  free description of this boundary.

## Composition

The helper delegates to existing boundaries:

- `build_postgresql_insert_statement()` creates insert statement metadata from
  `PersistenceInput`.
- The PostgreSQL execution adapter boundary creates execution-plan metadata
  through the disabled runtime adapter.
- The default PostgreSQL transaction policy contributes future single-batch
  caller-provided-session policy metadata.
- The default PostgreSQL idempotency/conflict strategy contributes Phase 1
  fail-on-conflict metadata without SQL mutation.
- `build_postgresql_disabled_runtime_execution_result()` produces the final
  disabled/no-execution runtime result.

The helper does not duplicate SQL generation logic and does not mutate SQL into
conflict, skip, or upsert behavior.

## Preview Result Semantics

A disabled preview may preserve:

- Source family and source ID.
- Attempted record count.
- Insert build status.
- Target table name.
- Record count and statement count.
- SQL text as preview metadata only.
- Execution plan metadata.
- Transaction policy metadata.
- Idempotency/conflict strategy metadata.
- Warning or error issues explaining disabled or non-ready outcomes.

The result must not imply records were persisted, written, committed, rolled
back, skipped, upserted, or run as a database operation. It must not return a
successful `PersistenceResult`.

## Non-Ready Outcomes

If the insert statement builder is not ready, the repository preview returns a
deterministic non-executing result:

- `no_records` when `PersistenceInput.records` is empty.
- `failed` when record shape validation prevents insert statement metadata.
- `unsupported` when a future unsupported insert-builder status is surfaced.

In all cases, `no_execution` remains true and no ready runtime persistence
semantics are produced.

## Relationship To Repository Behavior

`PostgreSQLPersistenceRepository` remains a skeleton that satisfies the
`PersistenceRepository` protocol while returning unsupported results. This
preview helper is a diagnostic boundary for future planning, not a repository
write method.

Future work that changes repository runtime behavior must still satisfy the
PostgreSQL implementation safety gate and must be scoped separately with
explicit connection, transaction, conflict, integration-test, and operational
reporting decisions.

## Related Documents

- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Disabled Runtime Execution Adapter Boundary](postgresql-disabled-runtime-execution-adapter-boundary.md)
- [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Idempotency Conflict Strategy Boundary](postgresql-idempotency-conflict-strategy-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
