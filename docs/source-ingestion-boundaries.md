# Source Ingestion Boundaries

CarbonOps-Parser is a documentation-first reference project for scheduled carbon factor source ingestion and parsing. This document defines the boundary between source discovery, download, parsing, validation, storage, and implementation-specific work.

## Purpose

The purpose of this document is to keep source ingestion work source-aware, traceable, and reviewable.

The project may discover, retrieve, archive, parse, validate, and persist selected public source documents. It should not imply official approval by source owners.

## Scope

Source ingestion covers:

- Discovering public source files and their structure.
- Retrieving source documents when a configured source is enabled.
- Archiving raw files outside the database.
- Parsing source-specific structures.
- Validating parsed records.
- Persisting shared ingestion metadata and source-specific master/detail records.

Phase 1 targets PostgreSQL for implemented persistence. The configuration model may describe PostgreSQL, MySQL, and SQL Server conceptually, but only PostgreSQL is in scope for Phase 1 implementation.

## Supported Source Families

Phase 1 focuses on three source families:

- GHG Protocol
- DEFRA / DESNZ
- IPCC EFDB

Each source family should have independent schedule settings, version or hash checks, archive paths, parser logic, validation rules, and source-specific storage boundaries.

## Source Discovery Boundary

Source discovery identifies public file structure before parser implementation.

Discovery may collect:

- Source family.
- Source URL or file reference.
- File name and content type.
- File size and hash when available.
- Workbook sheet names or export sections.
- Header rows and column names.
- Sample rows.
- Candidate data regions.
- Potential master/detail relationships.

Discovery should not persist parsed factor records as completed ingestion output. It should produce notes, fixtures, or mapping observations that can be reviewed before parser behavior is finalized.

## Download And Cache Boundary

Download and cache behavior should retrieve public source documents only after configuration and database startup checks have completed.

The raw file archive should store the downloaded file in a configured filesystem path. The database should store metadata about the file, not the raw document body.

Download behavior should support idempotency by checking source version, publication date when available, and content hash when practical. If the same source version and hash are already known, ingestion should skip duplicate processing.

## Parser Boundary

Parser logic should remain source-specific.

GHG Protocol, DEFRA / DESNZ, and IPCC EFDB may use different parser modules, mapping rules, and intermediate structures. Shared parser helpers should be introduced only when they reduce real duplication without hiding source-specific meaning.

The parser must preserve source traceability. It should avoid silently transforming records without validation issues, mapping notes, or normalization notes that explain the change.

## Validation And Normalization Boundary

Validation should check whether parsed records are complete, interpretable, and safe to persist for the intended source-specific model.

Validation output should identify:

- Source family.
- Source version or file reference when available.
- Record location when available.
- Field or value being checked.
- Severity.
- Reason.

Normalization should be conservative. Shared normalization may standardize technical fields such as whitespace, timestamps, hashes, and status values, but it should not erase source-specific categories, units, references, or context.

Source-specific ingestion should stay isolated from shared validation and normalization so that source-owner structures remain traceable.

## Storage Boundary

Storage should use shared ingestion metadata tables plus source-specific master/detail tables.

The intended source-specific table groups are:

- `ghg_*` for GHG Protocol.
- `defra_*` for DEFRA / DESNZ.
- `ipcc_*` for IPCC EFDB.

This task documents the intended boundary only. It does not add database migrations, schema files, or runtime persistence behavior.

Phase 1 should not force all source families into one canonical factor table. A future normalized or search-oriented projection may be considered separately.

## Ingestion Metadata Boundary

Shared ingestion metadata should track the processing lifecycle across source families.

Metadata should include, where available:

- Source family.
- Source URL or file reference.
- Version or publication date.
- Retrieval timestamp.
- Raw file path.
- Raw file hash.
- Parser version.
- Processing status.
- Import run summary.
- Validation issue summary.

Metadata should support idempotency, traceability, and operational review. It should not replace source-specific master/detail records.

## Python And .NET Implementation Boundary

The Python and .NET implementations are independent implementation options for the same conceptual workflow.

Python is planned first because it is better suited for early source discovery, file handling, spreadsheet inspection, and parser experimentation.

The .NET implementation should aim for conceptual parity later. It should not define a different product scope, source boundary, or assurance model.

Shared documentation should describe common concepts. Implementation-specific details should stay within `src/python` or `src/dotnet`.

## Out-Of-Scope Items

CarbonOps-Parser should not:

- Provide emissions advice.
- Provide legal interpretation.
- Provide audit assurance.
- Provide compliance guarantees.
- Claim official source-owner approval.
- Replace source-owner documentation or source files.
- Store confidential or proprietary source data.
- Create a universal carbon accounting model.
- Normalize all source families into one canonical factor table during Phase 1.

## Review Checklist

Before source ingestion changes are reviewed, check that they:

- Stay within the selected source family boundary.
- Preserve raw source traceability.
- Run only after required database startup checks.
- Avoid duplicate imports when version and hash are unchanged.
- Keep parser behavior source-specific unless shared logic is clearly justified.
- Record validation issues or normalization notes for meaningful transformations.
- Keep shared metadata separate from source-specific records.
- Preserve Python and .NET implementation independence.
- Avoid new dependencies unless they are justified and documented.
- Avoid unsupported legal, accounting, reporting, or source-owner assurance claims.
