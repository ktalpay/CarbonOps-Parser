# PostgreSQL Persistence Schema Boundary

This document defines the logical PostgreSQL schema boundary for future persistence of normalized records.

It is a schema boundary only. It does not connect to PostgreSQL, execute SQL, create tables, run migrations, write records, read files, perform HTTP or network calls, schedule work, or use credentials.

## Purpose

`get_normalized_record_postgresql_schema()` exposes deterministic schema metadata for normalized persistence input. The descriptor is intentionally limited to a logical table name, logical column descriptors, and idempotency key field names.

The descriptor is not a migration, ORM model, SQL generator, database client, or runtime persistence implementation.

Repository implementations are also deferred. `PersistenceRepository` describes the future repository protocol, but no PostgreSQL repository implementation is added by the schema boundary.

## Logical Table

The current logical table name is:

- `normalized_records`

This table name is descriptive. It does not imply that a table exists or should be created by this package at runtime.

## Logical Columns

Future normalized record persistence is expected to include:

- `source_family`: source family from `PersistenceInput`
- `source_id`: source id from `PersistenceInput`
- `record_id`: normalized record identity
- `record_index`: parser or normalization record index when available
- `row_number`: source row number when available
- `normalized_fields`: structured normalized field payload
- `source_reference`: source reference metadata when available
- `source_artifact_reference`: future source artifact reference metadata
- `source_checksum_sha256`: future source checksum metadata
- `parser_metadata`: parser metadata when explicitly supplied
- `normalization_metadata`: normalization metadata when explicitly supplied
- `created_at`: future operational creation timestamp
- `updated_at`: future operational update timestamp

The descriptor uses logical type labels such as `text`, `jsonb`, and `timestamptz`. These labels are schema metadata for review and preview boundaries, not runtime table management behavior.

## DDL Preview Relationship

`render_postgresql_ddl_preview()` can render deterministic PostgreSQL DDL preview text from the logical descriptor.

The preview may include `CREATE TABLE` text, descriptor columns, nullability markers, and a unique constraint preview for descriptor idempotency fields. It remains review text only. It does not connect to PostgreSQL, execute SQL, create tables, run migrations, write records, load credentials, or add a database dependency.

Runtime schema ownership, migration tooling, repository writes, and conflict handling remain deferred.

## Idempotency Strategy

Future idempotency should be based on a stable combination of:

- source identity: `source_family`, `source_id`
- record identity: `record_id`
- source artifact context: `source_artifact_reference`
- source checksum context: `source_checksum_sha256`

Conflict handling remains deferred. Future work must decide whether conflicts are ignored, updated, versioned, rejected, or stored as separate import attempts.

## Deferred Runtime Work

Future PostgreSQL work must be separately scoped and should cover:

- schema migrations
- table ownership and naming policy
- indexes and uniqueness constraints
- transaction boundaries
- conflict handling
- import run identity
- idempotency keys
- operational timestamps
- error handling and retry policy
- database configuration and credential management

None of those runtime behaviors are implemented by this boundary.

## Repository Planning Relationship

The PostgreSQL repository implementation planning boundary defines the decisions required before this logical schema can be used by runtime repository code. Schema descriptors and DDL previews stay descriptive until a later task explicitly adds migrations, repository implementation, integration tests, and operational behavior.

The PostgreSQL implementation safety gate must be satisfied before this schema metadata is used by any runtime database write, migration, or repository implementation.

## Non-Goals

This boundary does not add:

- PostgreSQL connections.
- Database writes.
- SQL execution.
- Migrations.
- Table creation.
- PostgreSQL package dependencies.
- Credentials or secrets.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Database Model](database-model.md)
- [Database Startup](database-startup.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Public Safety](public-safety.md)
