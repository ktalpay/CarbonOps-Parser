# Database Model

CarbonOps-Parser uses PostgreSQL for Phase 1. The schema contract separates shared ingestion metadata from source-specific master/detail records.

The contract in this document is intentionally conceptual. The first SQL script should implement these table responsibilities without adding parser logic or runtime behavior to the documentation task that defines the contract.

## Design Rules

- Shared ingestion tables track operational metadata that applies to every source.
- Source-specific tables preserve the structure of each source family.
- Raw source files are archived on disk; PostgreSQL stores file metadata and hashes.
- Imports are idempotent by source version and raw file hash.
- Required tables must exist before scheduled source ingestion starts.

## Why There Is No Single Factor Table In Phase 1

GHG Protocol, DEFRA/DESNZ, and IPCC EFDB have different source structures, terminology, units, reference models, and workbook or export layouts. Phase 1 keeps their records in source-specific master/detail tables so each parser can preserve useful context from its own source.

A single canonical factor table at this stage would either lose source-specific detail or force premature assumptions about normalization. A later phase may add a normalized or search-oriented projection derived from the source-specific tables.

## Shared Ingestion Metadata Tables

Shared tables apply to all source families.

### `carbon_sources`

- Scope: shared.
- Purpose: stores one row per configured source family, such as GHG Protocol, DEFRA/DESNZ, and IPCC EFDB.
- Key fields: `id`, `source_key`, `display_name`, `source_family`, `is_enabled`, `created_at`, `updated_at`.
- Primary relationship: parent table for `carbon_source_versions`, `carbon_import_runs`, `carbon_raw_files`, and source-specific imported records through the relevant source/version context.

### `carbon_source_versions`

- Scope: shared.
- Purpose: records detected source versions and content hashes so imports can skip unchanged source files.
- Key fields: `id`, `source_id`, `version_key`, `source_url`, `content_sha256`, `detected_at`, `metadata`.
- Primary relationship: belongs to `carbon_sources`; referenced by `carbon_import_runs`, `carbon_raw_files`, and source-specific table rows that are tied to a detected source version.

### `carbon_import_runs`

- Scope: shared.
- Purpose: records each import attempt and its final status, summary counts, and error summary when applicable.
- Key fields: `id`, `source_id`, `source_version_id`, `status`, `started_at`, `completed_at`, `records_read`, `records_valid`, `records_rejected`, `summary`, `error_message`.
- Primary relationship: belongs to `carbon_sources` and usually to `carbon_source_versions`; parent for `carbon_validation_issues`; referenced by source-specific rows created during that import.

### `carbon_raw_files`

- Scope: shared.
- Purpose: stores metadata for archived source files without storing the raw file contents in PostgreSQL.
- Key fields: `id`, `source_id`, `source_version_id`, `import_run_id`, `archive_path`, `file_name`, `content_type`, `file_size_bytes`, `sha256`, `downloaded_at`.
- Primary relationship: belongs to `carbon_sources` and `carbon_source_versions`; may belong to `carbon_import_runs` when the file was downloaded as part of a run.

### `carbon_validation_issues`

- Scope: shared.
- Purpose: records parse, validation, and persistence-preparation issues found during an import.
- Key fields: `id`, `import_run_id`, `source_id`, `source_version_id`, `severity`, `issue_code`, `message`, `raw_location`, `record_context`, `created_at`.
- Primary relationship: belongs to `carbon_import_runs`; may also carry source/version context for easier review across import runs.

### `carbon_job_locks`

- Scope: shared.
- Purpose: supports the design-level lock concept for preventing overlapping jobs for the same source.
- Key fields: `id`, `lock_key`, `source_id`, `owner`, `acquired_at`, `expires_at`, `released_at`.
- Primary relationship: optionally belongs to `carbon_sources`; referenced by the background service at runtime to coordinate scheduled jobs.

## DEFRA/DESNZ Tables

DEFRA/DESNZ tables are source-specific and should preserve the category, subcategory, factor set, and factor value structure discovered in DEFRA/DESNZ source files.

### `defra_categories`

- Scope: source-specific DEFRA/DESNZ.
- Purpose: stores top-level DEFRA/DESNZ category records.
- Key fields: `id`, `source_version_id`, `category_code`, `category_name`, `display_order`, `metadata`.
- Primary relationship: belongs to `carbon_source_versions`; parent for `defra_subcategories`.

### `defra_subcategories`

- Scope: source-specific DEFRA/DESNZ.
- Purpose: stores nested category records below a DEFRA/DESNZ category.
- Key fields: `id`, `category_id`, `source_version_id`, `subcategory_code`, `subcategory_name`, `display_order`, `metadata`.
- Primary relationship: belongs to `defra_categories`; parent for `defra_factor_sets`.

### `defra_factor_sets`

- Scope: source-specific DEFRA/DESNZ.
- Purpose: groups related DEFRA/DESNZ factor values by source sheet, year, activity, unit, or other discovered grouping fields.
- Key fields: `id`, `subcategory_id`, `source_version_id`, `factor_set_key`, `factor_name`, `activity`, `unit`, `source_sheet`, `metadata`.
- Primary relationship: belongs to `defra_subcategories`; parent for `defra_factor_values`.

### `defra_factor_values`

- Scope: source-specific DEFRA/DESNZ.
- Purpose: stores individual DEFRA/DESNZ factor values and row-level measurement context.
- Key fields: `id`, `factor_set_id`, `source_version_id`, `greenhouse_gas`, `value`, `unit`, `year`, `raw_row_number`, `metadata`.
- Primary relationship: belongs to `defra_factor_sets`; tied back to a version through `carbon_source_versions`.

## GHG Protocol Tables

GHG Protocol tables are source-specific and should preserve tool, sheet, group, and factor value context discovered in GHG Protocol source files.

### `ghg_tools`

- Scope: source-specific GHG Protocol.
- Purpose: stores GHG Protocol tool or workbook records.
- Key fields: `id`, `source_version_id`, `tool_key`, `tool_name`, `tool_version`, `source_url`, `metadata`.
- Primary relationship: belongs to `carbon_source_versions`; parent for `ghg_factor_sheets`.

### `ghg_factor_sheets`

- Scope: source-specific GHG Protocol.
- Purpose: stores sheet-level structures within a GHG Protocol tool or workbook.
- Key fields: `id`, `tool_id`, `source_version_id`, `sheet_name`, `sheet_title`, `header_row`, `metadata`.
- Primary relationship: belongs to `ghg_tools`; parent for `ghg_factor_groups`.

### `ghg_factor_groups`

- Scope: source-specific GHG Protocol.
- Purpose: groups related GHG Protocol factor rows found within a sheet.
- Key fields: `id`, `factor_sheet_id`, `source_version_id`, `group_key`, `group_name`, `scope_label`, `metadata`.
- Primary relationship: belongs to `ghg_factor_sheets`; parent for `ghg_factor_values`.

### `ghg_factor_values`

- Scope: source-specific GHG Protocol.
- Purpose: stores individual GHG Protocol factor values and row-level context.
- Key fields: `id`, `factor_group_id`, `source_version_id`, `factor_name`, `greenhouse_gas`, `value`, `unit`, `raw_row_number`, `metadata`.
- Primary relationship: belongs to `ghg_factor_groups`; tied back to a version through `carbon_source_versions`.

## IPCC EFDB Tables

IPCC EFDB tables are source-specific and should preserve sector, category, reference, factor record, and factor value context. IPCC EFDB is expected to be more heterogeneous than the other Phase 1 source families, so these table responsibilities may be refined after discovery.

### `ipcc_sectors`

- Scope: source-specific IPCC EFDB.
- Purpose: stores top-level IPCC EFDB sector records.
- Key fields: `id`, `source_version_id`, `sector_code`, `sector_name`, `display_order`, `metadata`.
- Primary relationship: belongs to `carbon_source_versions`; parent for `ipcc_categories`.

### `ipcc_categories`

- Scope: source-specific IPCC EFDB.
- Purpose: stores category records within an IPCC EFDB sector, including nested category context when present.
- Key fields: `id`, `sector_id`, `parent_category_id`, `source_version_id`, `category_code`, `category_name`, `metadata`.
- Primary relationship: belongs to `ipcc_sectors`; may reference another `ipcc_categories` row for hierarchy; parent for `ipcc_factor_records`.

### `ipcc_references`

- Scope: source-specific IPCC EFDB.
- Purpose: stores reference and citation metadata used by IPCC EFDB factor records.
- Key fields: `id`, `source_version_id`, `reference_key`, `title`, `authors`, `publication_year`, `source_detail`, `metadata`.
- Primary relationship: belongs to `carbon_source_versions`; referenced by `ipcc_factor_records` when a factor record has citation context.

### `ipcc_factor_records`

- Scope: source-specific IPCC EFDB.
- Purpose: stores IPCC EFDB factor records with sector/category and reference context.
- Key fields: `id`, `category_id`, `reference_id`, `source_version_id`, `record_key`, `description`, `region`, `technology`, `parameters`, `metadata`.
- Primary relationship: belongs to `ipcc_categories`; may belong to `ipcc_references`; parent for `ipcc_factor_values`.

### `ipcc_factor_values`

- Scope: source-specific IPCC EFDB.
- Purpose: stores individual IPCC EFDB factor values and measurement context.
- Key fields: `id`, `factor_record_id`, `source_version_id`, `greenhouse_gas`, `value`, `unit`, `uncertainty`, `raw_location`, `metadata`.
- Primary relationship: belongs to `ipcc_factor_records`; tied back to a version through `carbon_source_versions`.

## Future Normalized/Search Projection

A future phase may add a normalized or search-oriented projection that makes common cross-source lookup easier. That projection should be derived from shared metadata and source-specific master/detail tables.

The projection should not replace the source-specific tables in Phase 1.
