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
- deterministic PostgreSQL insert statement builder data without execution
- PostgreSQL persistence preview result data without execution
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

## Connection Session Contract Relationship

`PostgreSQLConnectionSession` defines a driver-neutral future caller-provided
session protocol. It is contract-only: it does not import a database driver,
open a connection, run SQL, load configuration, load credentials, or change
`PostgreSQLPersistenceRepository` runtime behavior.

Future repository execution adapters may consume this contract only after this
safety gate is satisfied in a separately scoped task.

## Insert Builder Relationship

`build_postgresql_insert_statement()` may produce deterministic SQL text with
placeholders and ordered parameter values for review and future repository use.
It is not an execution path and must not be wired to a database connection,
cursor, migration runner, credential loader, or repository write behavior before
this gate is satisfied.

## Execution Adapter Boundary Relationship

`PostgreSQLExecutionPlan` may describe how insert-builder output would be handed
to a future caller-provided session. It is no-execution metadata only and must
not become a database connection, SQL runtime, transaction boundary, migration
runner, or repository write path before this gate is satisfied.

## Transaction Policy Relationship

`PostgreSQLTransactionPolicy` may describe future single-batch, caller-provided
session, no-partial-success policy. It is policy metadata only and must not
become real transaction start, completion, rollback, SQL runtime, or repository
write behavior before this gate is satisfied.

## Persistence Preview Relationship

`build_postgresql_persistence_preview()` may expose insert-builder output through
a preview-specific result model. It must remain separate from
`PersistenceResult` repository execution semantics and must not call
`PostgreSQLPersistenceRepository.persist()`.

`carbonops-parser local-dry-run --include-postgresql-preview` may display that
preview result for the checked-in local fixture path. This is output-only
preview behavior and must not become a database connection, SQL execution, or
repository write path before this gate is satisfied.

## Forbidden Before Gate Approval

Before this gate is satisfied, future changes must not add:

- Implicit local database writes.
- A production database target.
- Database credentials, secrets, or connection strings in the repository.
- Automatic migrations or table creation.
- SQL execution from DDL preview helpers.
- SQL execution from schema descriptor helpers.
- SQL execution from insert statement builder helpers.
- SQL execution from persistence preview helpers.
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

The [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
breaks these steps into proposed follow-up tasks and records dependency,
transaction, conflict, schema lifecycle, integration test, and observability
decisions for future runtime work. It is planning-only and does not satisfy this
gate by itself.

The [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
selects a preferred future driver direction without adding the dependency,
importing a driver, connecting to PostgreSQL, or enabling runtime writes.

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
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL Execution Adapter Boundary](postgresql-execution-adapter-boundary.md)
- [PostgreSQL Transaction Policy Boundary](postgresql-transaction-policy-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [PostgreSQL Insert SQL Builder Boundary](postgresql-insert-sql-builder-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Public Safety](public-safety.md)
