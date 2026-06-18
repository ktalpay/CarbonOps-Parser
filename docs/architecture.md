# Architecture

CarbonOps-Parser is organized around scheduled carbon factor source ingestion. The project checks configured public source families, detects source changes, downloads changed documents, archives raw files, parses source-specific structures, validates parsed records, and persists both shared ingestion metadata and source-specific records.

The public architecture is intentionally non-destructive by default. Local examples and dry-run paths can inspect carbon accounting emission factor fixtures, parser handoffs, validation issues, PostgreSQL schema metadata, and SQL previews without making network calls, connecting to PostgreSQL, executing SQL, loading production credentials, or claiming production carbon-accounting correctness.

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

- Python package code in `src/carbonfactor_parser`
- .NET contracts and future Worker Service path in `src/dotnet`

Both implementations should follow the same conceptual workflow, but they may use language-appropriate structure and tooling.

The Python implementation is developed first because it is well suited to early source discovery, Excel inspection, parser mapping, and data engineering workflows.

The .NET implementation is an independent Worker Service path for users who prefer a typed background service architecture.

The Python and .NET implementations should not depend on each other.

Shared contract names, statuses, issue semantics, diagnostics, and serialized field expectations are kept reviewable through parity tests and parity review documents. A runtime slice can be Python-first only when the task explicitly allows it and records the parity impact.

## Runtime Readiness And Diagnostics

Phase 1 separates readiness checks from execution:

- Source acquisition can validate descriptors and plan local dry-run targets without acquiring content by default.
- Parser execution can consume already-loaded local content and report structured parser validation issues.
- Normalization and persistence handoffs keep raw parser output, normalized fields, source provenance, and persistence input metadata separate.
- PostgreSQL bootstrap and readiness boundaries expose schema descriptors, DDL previews, runtime config gates, disabled execution adapters, and opt-in integration checks before any database write path is promoted.
- Operational diagnostics expose run identity, status, issue counts, and failure context while avoiding production credentials and private source data.

This posture lets first-time reviewers inspect data ingestion, validation, and PostgreSQL readiness behavior without source-owner credentials or production infrastructure.

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
