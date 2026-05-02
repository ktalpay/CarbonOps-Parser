# Database Model

CarbonOps-Parser uses PostgreSQL for Phase 1. The database model separates shared ingestion metadata from source-specific master/detail records.

## Shared Ingestion Tables

The shared tables track sources, source versions, raw files, import runs, validation issues, and job locks.

### `carbon_sources`

Stores configured source family records such as GHG Protocol, DEFRA/DESNZ, and IPCC EFDB.

Expected responsibilities:

- Source key
- Display name
- Enabled state
- Source family metadata

### `carbon_source_versions`

Tracks detected source versions and hashes.

Expected responsibilities:

- Source reference
- Version key
- Source URL or discovery reference
- SHA-256 hash
- Detected timestamp

### `carbon_import_runs`

Tracks each attempted import.

Expected responsibilities:

- Source reference
- Source version reference
- Run status
- Started and completed timestamps
- Summary counts
- Error summary when applicable

### `carbon_raw_files`

Stores metadata for archived raw files. Raw source files should be stored on disk, not directly in database tables.

Expected responsibilities:

- Source/version reference
- Archive path
- File name
- Content type
- File size
- SHA-256 hash
- Downloaded timestamp

### `carbon_validation_issues`

Stores validation issues found during parsing or persistence preparation.

Expected responsibilities:

- Import run reference
- Source-specific record reference when available
- Severity
- Issue code
- Message
- Raw location or row context when available

### `carbon_job_locks`

Supports the design-level concept of preventing overlapping imports for the same source.

Expected responsibilities:

- Lock key
- Owner
- Acquired timestamp
- Expiration timestamp

## Source-Specific Tables

Phase 1 should not force all source records into one canonical factor table. Each source family keeps its own table group because the source structures differ.

Initial DEFRA/DESNZ table group:

- `defra_categories`
- `defra_subcategories`
- `defra_factor_sets`
- `defra_factor_values`

Initial GHG Protocol table group:

- `ghg_tools`
- `ghg_factor_sheets`
- `ghg_factor_groups`
- `ghg_factor_values`

Initial IPCC EFDB table group:

- `ipcc_sectors`
- `ipcc_categories`
- `ipcc_references`
- `ipcc_factor_records`
- `ipcc_factor_values`

These groups may be refined after source discovery inspects real source file structures.

## Future Projection

A later phase may add a normalized or search-oriented projection to support common lookup scenarios. That projection should be derived from source-specific records and should not replace source-specific master/detail storage in Phase 1.
