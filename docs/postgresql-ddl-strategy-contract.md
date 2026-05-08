# PostgreSQL DDL Strategy Contract (Phase 1 Planning)

## Status

- Task: CO-106A
- Scope: Documentation-only contract for future PostgreSQL DDL naming, key, constraint, and index strategy.
- Implementation state: No runtime code, no migrations, and no executable SQL are introduced by this document.

## Purpose

This document defines a stable, implementation-agnostic DDL strategy contract for CarbonOps-Parser Phase 1 PostgreSQL planning. It provides naming, key, constraint, and index expectations that future Python and .NET implementations must preserve conceptually.

This contract extends:
- `docs/postgresql-phase1-schema-contract.md`
- `docs/postgresql-bootstrap-boundary.md`

## 1) Table Naming Convention

All PostgreSQL table names in this strategy contract must follow:

- `lowercase_snake_case` only.
- Explicit source-family prefixes where applicable (`ghg_`, `defra_`, `ipcc_`).
- Explicit `master`/`detail` intent in source-family table names.
- Shared/system metadata tables must be explicit and non-ambiguous.
- Names must avoid any implication of JSON-first, temporary, test-only, or manual-input workflows.

### Shared/system naming candidates

- `source_families`
- `ingestion_runs`
- `source_documents`
- `parser_runs`
- `bootstrap_schema_state`

### Source-family naming candidates

- GHG
  - `ghg_master`
  - `ghg_detail`
- DEFRA
  - `defra_master`
  - `defra_detail`
- IPCC
  - `ipcc_master`
  - `ipcc_detail`

These names are contract candidates for future DDL implementation and should remain stable unless superseded by a formal contract update.

## 2) Shared/System Table Responsibilities

### `source_families`

Responsibility:
- Canonical source-family/type lookup metadata (for example: GHG, DEFRA, IPCC and type variants).
- Stable join target for runs and source-document metadata where applicable.

### `ingestion_runs`

Responsibility:
- Acquisition/ingestion run identity and lifecycle metadata.
- Correlation identifiers and timestamps.
- High-level run status and error summary fields.

### `source_documents`

Responsibility:
- Source document acquisition identity and provenance metadata.
- Version identity (where source-published versioning exists).
- Document checksum/hash metadata for idempotency and change detection.
- Relationship anchor for family-specific master rows.

### `parser_runs`

Responsibility:
- Parser execution run identity and lifecycle status metadata.
- Parse error code/message metadata and correlation to ingestion/source-document context.

### `bootstrap_schema_state`

Responsibility:
- Bootstrap/check execution state metadata when schema startup checks are performed.
- Last-check status, timestamps, and non-destructive compatibility notes.

## 3) Source-Family Table Responsibilities

Each source family keeps a `master`/`detail` split:

- Master tables represent source/year/reporting-period/document-level records.
- Detail tables represent parsed factor/parameter rows linked to master rows.

### GHG

- `ghg_master`
  - Source/year/reporting-period/document-level metadata for GHG publications.
  - Link to `source_documents` and run metadata where applicable.
- `ghg_detail`
  - Parsed GHG calculation factors/parameters tied to `ghg_master`.

### DEFRA

- `defra_master`
  - Source/year/reporting-period/document-level metadata for DEFRA/DESNZ publications.
  - Link to `source_documents` and run metadata where applicable.
- `defra_detail`
  - Parsed DEFRA calculation factors/parameters tied to `defra_master`.

### IPCC

- `ipcc_master`
  - Source/year/reporting-period/document-level metadata for IPCC publications.
  - Link to `source_documents` and run metadata where applicable.
- `ipcc_detail`
  - Parsed IPCC calculation factors/parameters tied to `ipcc_master`.

## 4) Primary Key Strategy

Contract expectations:

- Surrogate primary keys are preferred for operational joins (UUID or generated identity are both conceptually acceptable).
- Selected PK mechanism must be representable consistently in both Python and .NET implementations.
- Natural business identity fields are still required but should typically be enforced as unique constraints (not necessarily as primary keys).
- No runtime-specific PK assumptions are allowed in the contract (for example, assumptions tied only to one ORM).

## 5) Foreign Key Strategy

Expected FK relationships:

- Detail -> master for each source family:
  - `ghg_detail` -> `ghg_master`
  - `defra_detail` -> `defra_master`
  - `ipcc_detail` -> `ipcc_master`
- Master -> source document metadata where applicable:
  - `*_master` -> `source_documents`
- Run metadata -> source family/type metadata where applicable:
  - `ingestion_runs` -> `source_families`
  - `parser_runs` -> `source_families`

FK behavior must prioritize referential integrity and deterministic join semantics.

## 6) Unique Constraint Strategy

Unique constraints must prevent duplicate persistence across repeated acquisition, parsing, and bootstrap-adjacent workflows.

Expected uniqueness targets:

- Source publication identity at master-level:
  - (`source_family_or_type`, `year_or_reporting_period`, `source_document_identity`, `source_document_version`)
- Source document identity at acquisition-level:
  - checksum/hash-based identity and source-document identity/version keys as applicable.
- Detail-level duplicate prevention:
  - Where natural detail fields are sufficient, enforce stable row uniqueness at the detail table level.

Unique constraints should support idempotent reprocessing without duplicate inserts.

## 7) Status/Lifecycle Field Expectations

Shared lifecycle/status metadata expectations:

- Acquisition status fields.
- Parse status fields.
- Bootstrap/check status fields where relevant.
- `created_at` and `updated_at` style timestamps.
- Structured error fields (`error_code`, `error_message`) where status can fail.
- Correlation and run identity fields (for example, `run_id`, `correlation_id`) for traceability.

## 8) Checksum/Hash Strategy

Contract expectations:

- Persist checksum/hash for downloaded source documents.
- Allow normalized parser-input checksum/hash as a future-ready field when needed.
- Use checksum/hash for idempotency and change detection decisions.
- Hash algorithm selection remains an implementation detail; however, persisted hash representation must be stable and deterministic across implementations.

## 9) Index Strategy

Index design should prioritize Phase 1 query and reconciliation needs.

Expected index targets:

- Source family/type selectors.
- Year/reporting-period selectors.
- Acquisition status selectors.
- Parse status selectors.
- Checksum/hash lookups.
- Created/updated timestamp filters/sorts.
- Master/detail FK join columns.

Indexes should be aligned to deterministic lookup and reprocessing workflows, not ad hoc temporary/test/manual data exploration flows.

## 10) Safety and Non-Goals

This CO-106A task explicitly does **not** include:

- Destructive schema operations.
- Any drop/truncate strategy.
- Automatic incompatible schema rewrite behavior.
- Executable DDL.
- Migrations.
- Runtime implementation code.
- Any fake/test/sample/manual data flow definition.

## 11) Python/.NET Parity Contract

Both Python and .NET implementations must follow the same conceptual persisted-schema contract for:

- Table naming semantics.
- Master/detail ownership boundaries.
- PK/FK/unique-constraint intent.
- Lifecycle status metadata semantics.
- Checksum/hash idempotency semantics.
- Index intent and query-orientation.

Language-specific ORM or tooling differences must not alter persisted schema meaning.
Future implementation agents should treat this document as a normative contract for Phase 1 DDL strategy behavior.

## 12) Cross References

- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
- [PostgreSQL Bootstrap Boundary Contract (Phase 1)](postgresql-bootstrap-boundary.md)
