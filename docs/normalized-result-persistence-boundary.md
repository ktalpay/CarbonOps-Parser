# Normalized Result Persistence Boundary

This document defines the persistence handoff boundary for normalized results.

It is a persistence input contract only. It does not connect to PostgreSQL, write records, create tables, generate SQL, run migrations, read files, perform HTTP or network calls, schedule work, or use credentials.

## Purpose

`PersistenceInput` represents normalized records prepared for a future persistence layer. It is built from already-computed `NormalizationResult` values.

`PersistenceInputRecord` preserves:

- source family
- source id
- normalized record id
- record index when available
- row number when available
- normalized fields from the existing `NormalizedRecord.fields` shape
- source reference when available
- parser metadata when explicitly supplied
- normalization metadata when explicitly supplied

## Build Result

`build_persistence_input_from_normalization_result()` returns `PersistenceInputBuildResult`.

Status values are:

- `ready` when normalized records contain consistent source identity
- `failed` when normalization has error issues or normalized records lack required source identity
- `no_records` when the normalization result has no records
- `not_ready` for reserved future boundary states that are neither failed nor ready

Failed and no-records normalization results do not produce ready persistence input.

## Source And Record Identity

The builder expects normalized records to carry `source_family` and `source_id` fields. Those values become the persistence input source identity.

`record_index` and `row_number` are copied from normalized fields when present. They are not inferred from record position.

The boundary currently expects one source identity per `PersistenceInput`. Mixed source identity is reported as a failed build result. Future idempotency keys, source version identity, import run identity, and storage partitioning remain separate concerns.

## Metadata

Parser and normalization metadata may be passed explicitly as in-memory mappings. The builder copies those mappings into the resulting persistence input and records.

The boundary does not discover metadata from files, configuration, environment variables, credentials, database state, or remote services.

## Deferred Runtime Work

PostgreSQL integration is a later task. Future runtime work must define schema ownership, transactions, idempotency keys, conflict handling, migrations, retry policy, and operational error handling behind separate scope.

This boundary does not include connection settings, SQL statements, table names, migration names, secrets, or database client dependencies.

## PostgreSQL Schema Boundary

`get_normalized_record_postgresql_schema()` exposes a logical PostgreSQL schema descriptor for future normalized record persistence. It provides the descriptive table name `normalized_records`, logical column descriptors, and future idempotency key fields.

The descriptor does not generate executable SQL, create migrations, connect to PostgreSQL, or write records. Runtime PostgreSQL integration remains deferred to a separate task.

## Repository Protocol Boundary

`PersistenceRepository` defines the future repository protocol for accepting `PersistenceInput` and returning `PersistenceResult`.

The package exposes repository result contracts and statuses only. It does not include a concrete PostgreSQL repository implementation, and it does not perform runtime persistence.

The PostgreSQL repository implementation planning boundary documents the decisions required before a concrete repository can be added.

## Non-Goals

This boundary does not add:

- Database connections.
- Database writes.
- SQL generation.
- Table creation.
- Migrations.
- PostgreSQL dependency changes.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.

## Related Documents

- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Normalization Input Boundary](normalization-input-boundary.md)
- [Normalization Boundary](normalization-boundary.md)
- [Database Model](database-model.md)
- [Database Startup](database-startup.md)
- [Public Safety](public-safety.md)
