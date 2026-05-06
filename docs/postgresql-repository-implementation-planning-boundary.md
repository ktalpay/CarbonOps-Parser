# PostgreSQL Repository Implementation Planning Boundary

This document defines the planning boundary for a future PostgreSQL `PersistenceRepository` implementation.

It is planning documentation only. It does not add a PostgreSQL repository, connect to a database, execute SQL, generate executable SQL, create tables, run migrations, write records, read files, perform HTTP or network calls, schedule work, or use credentials.

## Purpose

`PersistenceRepository` now defines the repository protocol for future persistence implementations. `get_normalized_record_postgresql_schema()` defines logical schema metadata for normalized records, and `render_postgresql_ddl_preview()` can render review-only DDL text from that descriptor.

A PostgreSQL repository implementation must be planned separately before runtime code is added. This document records the decisions that must be made and the safe sequence for later implementation.

## Required Design Decisions

Future PostgreSQL repository work must decide:

- Sync vs async: whether the repository is synchronous, asynchronous, or exposed behind separate sync and async adapters.
- Driver choice: database driver selection remains deferred until runtime requirements, deployment targets, and test strategy are known.
- Config ownership: connection settings must belong to an explicit configuration boundary, not to parser, normalization, or persistence input contracts.
- Credential loading: secret handling remains deferred and must not be implicit in repository construction.
- Transaction boundary: whether one `PersistenceInput` maps to one transaction, chunked transactions, or caller-managed transactions.
- Table creation and migrations: schema migration ownership must be separate from repository writes.
- Idempotency enforcement: source identity, record identity, artifact reference, checksum metadata, and import context need explicit key policy.
- Conflict handling: later work must decide whether conflicts are ignored, updated, versioned, rejected, or reported as partial failures.
- Batch insert behavior: later work must define batch size, ordering, chunking, and memory limits.
- Partial failure behavior: later work must define how attempted, persisted, skipped, and failed record counts are reported.
- Retry behavior: retry policy must be external or explicitly scoped; it should not be hidden inside basic repository calls.
- Logging and audit metadata: later work must define what metadata is logged, stored, redacted, or returned in `PersistenceResult.repository_metadata`.

## Explicit Non-Goals

This planning boundary does not add:

- Database connections.
- SQL execution.
- Executable SQL generation.
- Migrations.
- Table creation.
- Runtime writes.
- PostgreSQL dependencies.
- Configuration loading.
- Credential or secret handling.
- File reading.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Future Implementation Sequence

A conservative future sequence is:

1. DDL preview boundary: use the existing review-only schema text helper without database access.
2. Repository implementation behind explicit config: add a concrete repository only after configuration and credential ownership are scoped.
3. Integration tests with a test database only: keep tests explicit, isolated, and disabled from accidental local or remote database access.
4. Idempotency and conflict handling: implement key enforcement and conflict result reporting after schema ownership is settled.
5. Operational hardening: add retry policy, transaction tuning, observability, audit metadata, and failure diagnostics behind explicit scope.

Each step should remain small, reviewable, and separately validated.

## Relationship To Existing Boundaries

`PersistenceInput` is the input shape. It is not a database command.

`PersistenceRepository` is the protocol. It does not require a PostgreSQL implementation to exist.

`PostgreSQLPersistenceSchema` is logical metadata. The DDL preview helper renders that metadata as review text only and does not imply table creation.

`PersistenceResult` is the repository result boundary. It should report attempted and persisted counts, issues, and repository metadata without exposing credentials or connection internals.

## Review Checklist

Future implementation PRs should confirm:

- Database access is explicit and test-isolated.
- No credentials are committed, logged, or embedded in examples.
- SQL execution, if added, is part of an explicitly scoped runtime task.
- Migrations are owned by a migration boundary, not hidden inside repository calls.
- Idempotency and conflict behavior are documented and tested.
- Partial failures are represented in `PersistenceResult`.
- Public safety checks pass.

## Related Documents

- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Database Model](database-model.md)
- [Database Startup](database-startup.md)
- [Public Safety](public-safety.md)
