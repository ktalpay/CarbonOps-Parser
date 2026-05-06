# PostgreSQL Implementation Safety Gate

This document defines the safety gate that must be satisfied before any runtime
PostgreSQL `PersistenceRepository` implementation, database connection, SQL
execution, migration, or database write is added.

It is safety-gate documentation only. It does not add runtime PostgreSQL
repository behavior, connect to a database, write records, execute SQL, run
migrations, load configuration, load credentials, add database dependencies,
perform HTTP or network calls, trigger source acquisition, or schedule work.

## Purpose

Current persistence work is intentionally limited to:

- `PersistenceInput`
- PostgreSQL logical schema descriptors
- review-only PostgreSQL DDL preview text
- `PersistenceRepository` protocol and `PersistenceResult` contracts
- `PostgreSQLPersistenceRepository` skeleton returning unsupported results only
- explicit caller-provided `PostgreSQLPersistenceOptions` with validation only
- default-disabled PostgreSQL integration test boundary metadata
- PostgreSQL repository planning documentation

Before any runtime PostgreSQL behavior is added, the preconditions in this gate must be reviewed and satisfied in a separate task.

## Mandatory Preconditions

Runtime database writes must not be added until all of the following are explicitly approved and documented:

- Explicit user configuration: database target selection must come from a deliberate user-controlled configuration boundary.
- No default DB target: the package must not assume a localhost, development, staging, production, or cloud database by default.
- Test database first: initial integration must target an explicit isolated test database only.
- Clear environment naming: test, local, staging, and production labels must be unambiguous and visible in configuration and logs.
- Migration and table ownership: table creation, schema migration ownership, and rollback ownership must be clarified before writes.
- Idempotency strategy: source identity, record identity, artifact reference, checksum, and conflict keys must be approved.
- Conflict handling: ignore, update, reject, version, or partial-failure behavior must be approved.
- Transaction behavior: transaction scope, batching, caller-managed transactions, and rollback boundaries must be approved.
- Failure and rollback behavior: partial failures, retry boundaries, rollback behavior, and persisted count reporting must be approved.
- Credential loading approach: secret source, redaction, local development behavior, and CI/test behavior must be approved.
- Operational logging and audit boundary: audit metadata, log redaction, correlation IDs, and repository metadata must be approved.

## Config Contract Relationship

`PostgreSQLPersistenceOptions` records caller-provided connection-shaped values
for future repository work. It does not load environment variables, read config
files, load credentials, connect to PostgreSQL, or execute SQL.

The options contract deliberately uses `password_set` instead of storing a
password value. Future runtime credential loading remains blocked until this
safety gate approves the credential source, redaction behavior, and test
isolation rules.

## Integration Test Relationship

PostgreSQL integration tests must be skipped by default. The current integration
test boundary exposes only a marker name, skip reason, and explicit opt-in
metadata. It does not read environment variables, load config, load credentials,
connect to PostgreSQL, execute SQL, or write records.

Future integration test wiring must require explicit opt-in and an isolated test
database before any connection behavior is introduced.

## Forbidden Before Gate Approval

Before this gate is satisfied, future changes must not add:

- Implicit local database writes.
- A production database target.
- Database credentials, secrets, or connection strings in the repository.
- Automatic migrations or table creation.
- SQL execution from DDL preview helpers.
- SQL execution from schema descriptor helpers.
- PostgreSQL driver or ORM dependencies.
- Runtime database connection code.
- Network-backed source acquisition coupled directly to persistence.
- Scheduler or background behavior that can trigger persistence.

## Implementation Sequence After Gate Approval

After this safety gate is satisfied, implementation should remain incremental:

1. Repository skeleton with no database connection: keep the current concrete
   class shape unable to connect or write.
2. Explicit config model: introduce user-controlled database configuration without loading credentials implicitly.
3. Test DB integration only: add isolated integration tests against an explicit test database.
4. Idempotency enforcement: implement approved idempotency keys and verification behavior.
5. Limited insert path: add the narrowest insert behavior for `PersistenceInput` records.
6. Conflict handling: implement approved conflict behavior and structured `PersistenceResult` reporting.
7. Operational hardening: add logging, audit metadata, rollback diagnostics, retry boundaries, and failure observability.

Each step must remain separately reviewed and tested.

## Review Checklist

Any task that proposes PostgreSQL runtime behavior should answer:

- What database target is selected, and how does the user choose it?
- How is accidental local or production write behavior prevented?
- Which database is used in tests, and how is it isolated?
- Where are credentials loaded from, and how are they redacted?
- Who owns migrations and table creation?
- What transaction boundaries are used?
- What idempotency keys are enforced?
- What happens on conflicts?
- What happens on partial failure?
- What metadata is logged, returned, or stored?
- How does the change prove DDL preview text is not executed implicitly?

## Relationship To Existing Boundaries

`render_postgresql_ddl_preview()` remains review text only. It must not become a runtime SQL execution path.

`PostgreSQLPersistenceSchema` remains logical metadata. It must not connect to PostgreSQL or create tables.

`PostgreSQLPersistenceRepository` is a skeleton that satisfies the repository
protocol while returning `unsupported`. It remains outside runtime database
behavior because it does not connect, write, execute SQL, run migrations, load
configuration, or load credentials.

A future implementation that changes this skeleton into a runtime repository
must satisfy this gate first.

Local dry-run helpers may produce `PersistenceInput` and DDL preview metadata, but they must not call repository implementations or write to a database.

## Non-Goals

This safety gate does not add:

- Runtime PostgreSQL repository implementation.
- Database connections.
- Database writes.
- SQL execution.
- Migrations.
- Database dependencies.
- Configuration loading implementation.
- Credential or secret handling.
- File reading.
- HTTP or network behavior.
- Source acquisition integration.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Public Safety](public-safety.md)
