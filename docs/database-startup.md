# Database Startup

Both implementation paths must make the PostgreSQL schema available before any source ingestion starts.

This startup contract applies to:

- `src/python`
- `src/dotnet`

## Required Startup Sequence

The required startup sequence is:

1. Read configuration.
2. Validate the configured database provider.
3. Fail fast if the provider is not `postgres`.
4. Connect to PostgreSQL.
5. Check whether the required schema and tables exist.
6. Create missing tables before source schedules are allowed to run.
7. Initialize source schedules.
8. Start scheduled source version/hash checks.

Downloading, parsing, validation, persistence, and import summary creation must not start before the required schema is available.

## Provider Validation

The conceptual configuration model allows these provider names:

- `postgres`
- `mysql`
- `mssql`

Phase 1 implements only `postgres`. Any other provider should stop startup with this clear message:

```text
Unsupported database provider. Phase 1 supports postgres only.
```

The provider check must happen before any connection-specific ingestion work is attempted.

## Schema Availability

The startup check should cover:

- Shared ingestion metadata tables.
- DEFRA/DESNZ source-specific tables.
- GHG Protocol source-specific tables.
- IPCC EFDB source-specific tables.

If any required table is missing, the implementation should create it before source ingestion starts. This applies equally to the Python and .NET implementations, even though their application structure and configuration files may differ.

## Startup Boundary

Startup may validate configuration, connect to PostgreSQL, and create missing schema objects. Startup must not download source files, parse source documents, or import records until schema creation has completed successfully.
