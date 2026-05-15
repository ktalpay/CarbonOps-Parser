# PostgreSQL

PostgreSQL is the only database provider implemented in Phase 1.

The conceptual configuration model recognizes `postgres`, `mysql`, and `mssql`, but Phase 1 should fail fast for any provider other than `postgres`.

## Initial Schema Script

The initial schema script lives at:

```text
database/postgres/001_initial_schema.sql
```

The script creates the `carbonops` schema, enables `pgcrypto` for UUID generation, and creates the Phase 1 shared ingestion metadata tables plus source-specific DEFRA/DESNZ, GHG Protocol, and IPCC EFDB table groups.

## Schema Contract

The schema baseline should include:

- Shared ingestion metadata tables.
- Source-family ingestion year-state table for production E2E targeting.
- DEFRA/DESNZ source-specific master/detail tables.
- GHG Protocol source-specific master/detail tables.
- IPCC EFDB source-specific master/detail tables.

Raw source files should be archived on disk. PostgreSQL should store raw file metadata such as archive path, file name, content type, size, hash, downloaded timestamp, and source/version references.

See `../../docs/database-model.md` for the table-level contract.

## Startup Table Creation

Both implementation paths should validate the configured provider before touching source ingestion work. If the provider is not `postgres`, startup should fail fast with a clear message.

After provider validation, each implementation should connect to PostgreSQL, check the required schema and tables, and create missing tables before scheduled source ingestion starts.

This startup behavior belongs to both:

- `src/python`
- `src/dotnet`

The SQL contract should be shared by both implementation paths. Python and .NET may have different startup code, but they should create and use the same PostgreSQL schema.

Both implementations should use `001_initial_schema.sql` directly or equivalent startup table creation logic that stays aligned with it.
