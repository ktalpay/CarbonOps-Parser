# PostgreSQL Repository Skeleton Boundary

This document defines the boundary for `PostgreSQLPersistenceRepository`.

The class is a skeleton only. It satisfies the `PersistenceRepository` protocol and returns a structured unsupported `PersistenceResult`. It does not connect to PostgreSQL, write records, generate executable SQL, execute SQL, create tables, run migrations, load configuration, load credentials, add database dependencies, perform HTTP or network calls, or schedule work.

## Purpose

`PostgreSQLPersistenceRepository` gives future PostgreSQL persistence work a concrete package-level shape without adding runtime database behavior.

The skeleton exposes:

- `provider_name`, with deterministic value `postgresql`.
- optional caller-provided `PostgreSQLPersistenceOptions`.
- `persist(persistence_input)`, which accepts `PersistenceInput`.
- structured unsupported results with issue code `POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED`.
- metadata indicating that the class is a skeleton and does not perform runtime database work.

## Persist Behavior

`persist()` returns `PersistenceResultStatus.UNSUPPORTED`.

The result preserves:

- attempted record count from `len(persistence_input.records)`.
- persisted record count as `0`.
- an error issue explaining that PostgreSQL runtime persistence is not implemented.
- repository metadata for troubleshooting and review.

No persistence input record is written, transformed, or converted into executable database operations.

## Options Relationship

The skeleton may be constructed with `PostgreSQLPersistenceOptions`. The options
object is retained as explicit caller-provided metadata only.

Providing options does not trigger environment loading, config loading,
credential loading, database connection, SQL generation, SQL execution,
migrations, or writes. `persist()` still returns `unsupported`.

## Safety Relationship

This skeleton is allowed before the PostgreSQL implementation safety gate because it cannot connect, write, migrate, or execute SQL.

Any later change that introduces a driver, connection target, credential loading, table creation, migration ownership, SQL execution, idempotency enforcement, conflict handling, or runtime writes must satisfy the PostgreSQL implementation safety gate in a separate task.

## Non-Goals

This skeleton does not add:

- PostgreSQL runtime persistence.
- Database driver or ORM dependencies.
- Database connections.
- Database writes.
- Executable SQL generation.
- SQL execution.
- Table creation.
- Migrations.
- Configuration file loading.
- Credential or secret handling.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Public Safety](public-safety.md)
