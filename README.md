# CarbonOps-Parser

CarbonOps-Parser is a standalone public technical project for scheduled carbon factor source ingestion and parsing.

The project is independent from `carbonops-assistant`. It is not a continuation, module, plugin, or dependency of that project.

CarbonOps-Parser is documentation-first at this stage. It describes a reference workflow for checking public emission factor sources on schedules, downloading changed source files, archiving raw files, parsing source-specific structures, validating parsed records, and storing ingestion results in PostgreSQL.

## Implementation Options

The repository contains two independent implementation paths:

- `src/python`
- `src/dotnet`

These are alternative implementations of the same conceptual workflow. Users who clone or fork the repository should be able to choose the Python implementation or the .NET implementation. The implementations should not depend on each other.

## Phase 1 Scope

Phase 1 focuses on scheduled ingestion and parsing for these source families:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

The intended Phase 1 workflow is:

1. Read configuration.
2. Validate the database provider.
3. Connect to PostgreSQL.
4. Check whether required tables exist.
5. Create missing tables if needed.
6. Initialize source schedules.
7. Check source version and file hash.
8. Download a source document when a new version or hash is detected.
9. Archive the raw source file.
10. Parse source-specific structures.
11. Validate parsed records.
12. Persist shared ingestion metadata and source-specific records.
13. Store import summaries and validation issues.

Phase 1 uses shared ingestion metadata tables plus source-specific master/detail tables. It does not force GHG Protocol, DEFRA/DESNZ, and IPCC EFDB into one canonical factor table. A normalized search projection may be considered in a later phase.

## Non-Goals

CarbonOps-Parser does not calculate carbon inventories, produce emissions reports, replace official source documentation, certify source data correctness, or provide a deployment platform. It is a scheduled carbon factor ingestion and parsing reference project.

## Documentation

- [Architecture](docs/architecture.md)
- [Configuration Model](docs/configuration-model.md)
- [Background Job Model](docs/background-job-model.md)
- [Database Model](docs/database-model.md)
- [Database Startup](docs/database-startup.md)
- [Linux Service Setup](docs/linux-service-setup.md)
- [Source Support](docs/source-support.md)
- [Source Discovery](docs/source-discovery.md)
- [Roadmap](docs/roadmap.md)
- [Task Breakdown](docs/task-breakdown.md)
- [Limitations](docs/limitations.md)
- [Public Safety](docs/public-safety.md)
- [PostgreSQL Database Notes](database/postgres/README.md)
- [Python Implementation](src/python/README.md)
- [.NET Implementation](src/dotnet/README.md)
