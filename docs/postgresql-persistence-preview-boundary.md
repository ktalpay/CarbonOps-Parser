# PostgreSQL Persistence Preview Boundary

This document defines the PostgreSQL persistence preview boundary.

The preview layer connects `PersistenceInput` to the PostgreSQL insert SQL
builder and returns structured preview data. It does not connect to PostgreSQL,
execute SQL, write records, create tables, run migrations, load config files,
load credentials, add database dependencies, perform HTTP or network calls, or
schedule work.

## Purpose

`build_postgresql_persistence_preview()` accepts `PersistenceInput` and delegates
insert statement construction to `build_postgresql_insert_statement()`.

For ready input, it returns `PostgreSQLPersistencePreviewResult` with:

- preview status.
- insert builder status.
- target table name.
- SQL text with placeholders.
- ordered column names.
- ordered parameter rows.
- record count.
- idempotency key fields.
- conflict target metadata.

The preview model is not a repository result and does not imply that records
were persisted.

## Status Values

`PostgreSQLPersistencePreviewStatus` values are:

- `ready`
- `failed`
- `no_records`
- `unsupported`

The preview status mirrors the insert builder status. If the insert builder is
not ready, the preview result is not ready and does not contain ready SQL
preview data.

## Builder Relationship

The preview layer must not duplicate SQL construction logic. It delegates to
`build_postgresql_insert_statement()` and copies the resulting statement fields
into a preview-specific model.

This keeps SQL statement construction separate from repository execution and
keeps the preview result separate from `PersistenceResult`, whose semantics are
reserved for repository behavior.

## Repository Relationship

`PostgreSQLPersistenceRepository.persist()` remains unsupported and
no-execution. The preview layer does not call the repository and does not turn
the repository skeleton into runtime persistence.

Future repository work must satisfy the PostgreSQL implementation safety gate
before using preview data in an execution path.

## Local Dry-Run CLI Relationship

`carbonops-parser local-dry-run` may include PostgreSQL preview data only when
called with `--include-postgresql-preview`. The default local dry-run output
remains unchanged without that flag.

The CLI preview section is output integration only. It delegates to
`build_postgresql_persistence_preview()` after the local dry-run has produced
ready `PersistenceInput`. It does not call a repository, execute SQL, connect to
PostgreSQL, write records, run migrations, load config files, load credentials,
or perform network calls.

The JSON demo command uses `--json --include-postgresql-preview`. No PostgreSQL
server, database configuration, or credentials are required because the command
only renders already-built preview data.

If the local dry-run does not produce ready `PersistenceInput`, the CLI reports a
non-ready PostgreSQL preview section and omits ready SQL preview data.

## Non-Goals

This boundary does not add:

- Runtime PostgreSQL repository implementation.
- Database connections.
- Database writes.
- SQL execution.
- Table creation.
- Migrations.
- Database driver or ORM dependencies.
- Environment variable loading.
- Config file loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [Local Dry-Run CLI Boundary](local-dry-run-cli-boundary.md)
- [Public Safety](public-safety.md)
