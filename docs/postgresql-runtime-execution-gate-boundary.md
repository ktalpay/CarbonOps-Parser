# PostgreSQL Runtime Execution Gate Boundary

This document defines the PostgreSQL runtime execution enablement gate.

It is gate metadata documentation only. It does not create a PostgreSQL
connection, create a cursor, run SQL, write records, start a transaction, finish
a transaction, roll back a transaction, create tables, run migrations, load
environment variables, load configuration files, load credentials, perform HTTP
or network calls, schedule work, or claim production persistence readiness.

## Purpose

CO-102K adds an explicit runtime execution gate so future PostgreSQL execution
must be deliberate and separately reviewed. The default gate decision is
disabled/no-execution. A caller may provide enablement intent as metadata, but
this task still does not enable repository execution.

The current code boundary is:

- `PostgreSQLRuntimeExecutionGate`: caller-provided intent metadata.
- `PostgreSQLRuntimeExecutionGateDecision`: structured gate decision.
- `PostgreSQLRuntimeExecutionGateStatus`: disabled, blocked, or not-enabled
  status values.
- `evaluate_postgresql_runtime_execution_gate()`: pure gate evaluator.
- `describe_postgresql_runtime_execution_gate()`: side-effect-free boundary
  description.

## Default Behavior

With no caller intent, the gate returns:

- `status`: `disabled`
- `requested`: `False`
- `no_execution`: `True`
- `runtime_enabled`: `False`
- `connection_required_now`: `False`
- `session_required_now`: `False`

The decision also lists future components that must be reviewed before runtime
execution can exist, including safety-gate approval, runtime adapter work,
caller-provided session handling, opt-in integration test completion, and a
separate repository runtime persistence task.

## Caller-Provided Intent

The gate accepts explicit caller intent as metadata only:

- `requested=False` keeps runtime execution disabled.
- `requested=True` returns blocked metadata when required future components are
  incomplete.
- `requested=True` with all future metadata marked complete still returns a
  not-enabled/no-execution decision because this boundary does not activate
  repository execution.

The gate does not validate real credentials, read configuration, create a
session, call an adapter, or execute SQL.

## Relationship To Existing Boundaries

- `PostgreSQLPersistenceRepository.persist()` remains unsupported/no-execution
  and is not changed by this gate.
- `PostgreSQLDisabledRuntimeExecutionAdapter` remains the no-execution runtime
  metadata composer.
- `build_postgresql_repository_disabled_execution_preview()` may report
  repository-level disabled diagnostics, but it does not become repository
  execution.
- Future repository execution work must explicitly consume this gate and still
  satisfy the PostgreSQL implementation safety gate.
- Future PostgreSQL integration tests must remain default-disabled and opt-in
  until a scoped runtime task introduces database behavior.
- The runtime readiness checklist defines the go/no-go criteria before a future
  task may use this gate for real execution.

## Non-Goals

This gate does not add:

- Runtime PostgreSQL repository implementation.
- Database connections.
- Cursor creation.
- SQL execution.
- Database writes.
- Real transaction behavior.
- Migrations or table creation.
- Environment variable loading.
- Configuration file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler or background job behavior.

## Related Documents

- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Disabled Runtime Execution Adapter Boundary](postgresql-disabled-runtime-execution-adapter-boundary.md)
- [PostgreSQL Repository Disabled Execution Preview Boundary](postgresql-repository-disabled-execution-preview-boundary.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
