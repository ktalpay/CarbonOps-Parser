# PostgreSQL DDL Preview Boundary

This document defines the PostgreSQL DDL preview boundary for normalized persistence input.

It is preview-only. It does not connect to PostgreSQL, execute SQL, create tables, run migrations, write records, read files, perform HTTP or network calls, schedule work, load configuration, or use credentials.

## Purpose

`render_postgresql_ddl_preview()` renders deterministic PostgreSQL DDL text from `get_normalized_record_postgresql_schema()`.

The preview is intended for review and planning. It is not a migration, repository implementation, database client, schema management tool, or runtime persistence path.

## Input Boundary

The helper consumes `PostgreSQLPersistenceSchema`, which contains:

- a logical table name
- deterministic logical column descriptors
- idempotency key field names when available

It does not inspect `PersistenceInput`, normalized records, parser output, files, configuration, database connections, or environment variables.

## Preview Output

The preview may include:

- `CREATE TABLE` text for the logical table
- column names and logical PostgreSQL type labels from the descriptor
- `NOT NULL` markers for non-nullable descriptor columns
- a unique constraint preview for descriptor idempotency fields

The preview is deterministic for the same schema descriptor. It is deliberately conservative and reviewable, but it is not a runtime DDL authority.

## Idempotency Preview

When `PostgreSQLPersistenceSchema.idempotency_key_fields` is populated, the preview includes a unique constraint using those fields.

Conflict handling remains deferred. Future implementation work must still decide how conflicts are reported, ignored, updated, versioned, rejected, or retried.

## Deferred Runtime Work

Future work remains separately scoped for:

- migration ownership
- database driver selection
- repository implementation
- connection and credential configuration
- table creation policy
- index tuning
- transaction boundaries
- conflict handling
- integration tests with an explicit test database

None of that runtime behavior is added by the preview helper.

## Non-Goals

This boundary does not add:

- PostgreSQL connections.
- Database writes.
- SQL execution.
- Migrations.
- Runtime table creation.
- PostgreSQL package dependencies.
- Configuration or credential loading.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Public Safety](public-safety.md)
