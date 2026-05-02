# Architecture

CarbonOps-Parser is organized around scheduled carbon factor source ingestion. The project checks configured public source families, detects source changes, downloads changed documents, archives raw files, parses source-specific structures, validates parsed records, and persists both shared ingestion metadata and source-specific records.

## Ingestion Workflow

The conceptual workflow is:

1. Source schedule is evaluated.
2. Source version and content hash are checked.
3. Changed source documents are downloaded.
4. Raw source files are archived outside the database.
5. Source-specific parser reads the document structure.
6. Parsed records are validated.
7. Shared ingestion metadata is persisted.
8. Source-specific master/detail records are persisted.
9. Import summary and validation issues are stored.

The service must not download, parse, or import source documents before the required database schema is available.

## Implementation Split

The repository contains two independent implementation paths:

- `src/python`
- `src/dotnet`

Both implementations should follow the same conceptual workflow, but they may use language-appropriate structure and tooling.

The Python implementation is developed first because it is well suited to early source discovery, Excel inspection, parser mapping, and data engineering workflows.

The .NET implementation is an independent Worker Service path for users who prefer a typed background service architecture.

The Python and .NET implementations should not depend on each other.

## Data Architecture

Phase 1 uses shared ingestion metadata tables for operational tracking:

- `carbon_sources`
- `carbon_source_versions`
- `carbon_import_runs`
- `carbon_raw_files`
- `carbon_validation_issues`
- `carbon_job_locks`

Phase 1 also uses source-specific master/detail tables:

- `defra_*`
- `ghg_*`
- `ipcc_*`

This avoids forcing different source structures into a single factor table too early. A future phase may add a normalized search projection for common lookup scenarios.
