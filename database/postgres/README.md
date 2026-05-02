# PostgreSQL

PostgreSQL is the only database provider implemented in Phase 1.

The conceptual configuration model recognizes `postgres`, `mysql`, and `mssql`, but Phase 1 should fail fast for any provider other than `postgres`.

## Planned Contents

Initial schema scripts will live in this directory.

The schema baseline should include:

- Shared ingestion metadata tables.
- DEFRA/DESNZ source-specific master/detail tables.
- GHG Protocol source-specific master/detail tables.
- IPCC EFDB source-specific master/detail tables.

Raw source files should be archived on disk. PostgreSQL should store raw file metadata such as archive path, file name, content type, size, hash, downloaded timestamp, and source/version references.
