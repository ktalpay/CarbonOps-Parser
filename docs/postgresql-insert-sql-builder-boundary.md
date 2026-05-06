# PostgreSQL Insert SQL Builder Boundary

This document defines the PostgreSQL insert statement builder boundary.

The builder returns deterministic parameterized statement data for review and
future repository use. It does not connect to PostgreSQL, execute SQL, write
records, create tables, run migrations, load config files, load credentials, add
database dependencies, perform HTTP or network calls, or schedule work.

## Purpose

`build_postgresql_insert_statement()` accepts `PersistenceInput` and returns a
structured `PostgreSQLInsertBuildResult`.

For ready input, the result contains `PostgreSQLInsertStatement` with:

- SQL text using placeholders.
- ordered parameter rows.
- target table name from `PostgreSQLPersistenceSchema`.
- ordered column names from the logical schema descriptor.
- record count.
- idempotency key fields and conflict target metadata from the logical schema.

The statement model is data only. It is not a database command runner.

## Status Values

`PostgreSQLInsertBuildStatus` values are:

- `ready`: insert statement data was built.
- `failed`: input shape was invalid.
- `no_records`: no persistence records were provided.
- `unsupported`: reserved for future unsupported builder scenarios.

No ready statement is returned for failed or no-record input.

## Parameter Boundary

The builder preserves normalized fields and metadata as in-memory parameter
values. It does not serialize payloads, infer types, convert values, or inspect
database state.

Current parameters include the logical schema columns:

- source identity
- record identity
- record index and row number
- normalized field payload
- source reference metadata
- source artifact/checksum metadata when provided through parser metadata
- parser metadata
- normalization metadata
- deferred operational timestamp fields as `None`

## Relationship To Schema

The builder uses `get_normalized_record_postgresql_schema()` by default. The
schema descriptor controls target table name, column order, and idempotency key
fields.

DDL preview and insert statement building are separate preview boundaries. Both
produce deterministic text or data; neither executes SQL.

## Persistence Preview Relationship

`build_postgresql_persistence_preview()` delegates SQL statement construction to
this builder and returns preview-specific persistence data. The preview layer
must not duplicate SQL construction logic and must not execute the returned SQL
text.

## Non-Goals

This boundary does not add:

- PostgreSQL repository runtime behavior.
- Database connections.
- Database writes.
- SQL execution.
- Table creation.
- Migrations.
- Database driver or ORM dependencies.
- Config file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [Public Safety](public-safety.md)
