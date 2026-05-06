# Persistence Repository Boundary

This document defines the persistence repository protocol, result boundary, and
current PostgreSQL skeleton behavior.

It is a protocol and skeleton boundary only. It does not connect to a database,
execute SQL, generate executable SQL, create tables, run migrations, read files,
perform HTTP or network calls, schedule work, or use credentials.

## Purpose

`PersistenceRepository` describes repository implementations that accept
`PersistenceInput` and return `PersistenceResult`.

The protocol currently requires:

- `provider_name`
- `persist(persistence_input)`

The package now includes `PostgreSQLPersistenceRepository` as a concrete
skeleton. It satisfies the protocol but returns an unsupported result instead of
connecting to PostgreSQL or writing records. Tests may also use fake in-memory
repositories to prove protocol behavior.

`PostgreSQLPersistenceOptions` provides an explicit caller-provided options
shape for future PostgreSQL repository work. Options validation remains separate
from repository persistence and does not load environment variables, config
files, or credentials.

`PostgreSQLIntegrationTestBoundary` provides default-disabled metadata for
future PostgreSQL integration tests. It does not add database dependencies,
connections, SQL execution, or writes.

`build_postgresql_insert_statement()` provides deterministic parameterized
insert statement data for future repository work. It does not execute SQL or
write records.

`build_postgresql_persistence_preview()` wraps the insert builder in a
preview-only result. It does not call `PersistenceRepository.persist()` and does
not imply repository execution success.

## Result Boundary

`PersistenceResult` reports:

- `status`
- `attempted_record_count`
- `persisted_record_count`
- structured issues
- optional repository metadata

`PersistenceResultStatus` values are:

- `success`
- `failed`
- `no_records`
- `unsupported`

`PersistenceIssue` represents repository-level warnings or errors with code, message, severity, optional field name, and optional context.

## Relationship To Persistence Input

Repository implementations must accept `PersistenceInput`, not raw parser payloads or normalization input. This keeps parsing, normalization, persistence preparation, and repository behavior separate.

No-records inputs should return a structured no-records or failed result. Failed or not-ready persistence input build results should not be passed to a repository.

## Deferred Runtime Work

Future PostgreSQL work remains separately scoped. It must define connection management, transactions, SQL or ORM strategy, migrations, idempotency enforcement, conflict handling, credentials, and operational error handling.

This boundary does not provide any of those runtime behaviors.

## PostgreSQL Skeleton

`PostgreSQLPersistenceRepository` exposes deterministic `provider_name`
metadata and accepts `PersistenceInput` through `persist()`.

`persist()` returns:

- status `unsupported`.
- attempted record count from the input records.
- persisted record count `0`.
- issue code `POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED`.
- skeleton metadata indicating no database connection, runtime write, or
  migration runtime is present.

It must remain inert until a later gated task adds explicit runtime database
behavior.

## PostgreSQL Planning Boundary

Before a concrete PostgreSQL repository is added, future work must follow the PostgreSQL repository implementation planning boundary. That plan keeps driver selection, sync vs async behavior, configuration ownership, credentials, transactions, migrations, idempotency, conflict handling, partial failures, retry behavior, and audit metadata outside this protocol-only task.

The PostgreSQL implementation safety gate must also be satisfied before any concrete repository can connect to PostgreSQL, execute SQL, run migrations, or write records.

## Non-Goals

This boundary does not add:

- Runtime PostgreSQL repository implementation.
- Database connections.
- Database writes.
- SQL generation or execution.
- Table creation.
- Migrations.
- Configuration or credential loading.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Public Safety](public-safety.md)
