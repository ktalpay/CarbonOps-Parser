# Source Adapter Contract

CarbonOps-Parser uses source adapter concepts to keep source-family-specific discovery, retrieval, and parsing separate from shared validation, normalization, metadata, and persistence concerns. This document defines the conceptual contract only.

## Purpose

The purpose of a source adapter is to represent one source-family-specific ingestion boundary.

An adapter should make source-specific structure explicit while preserving enough context for downstream validation, metadata, and storage decisions.

## Scope

This document describes the expected responsibilities, handoff points, and review expectations for source adapters.

It does not define final code contracts, database schema, SQL files, ORM models, abstract classes, or implementation classes.

Phase 1 remains focused on documentation, source discovery, and early ingestion design. PostgreSQL is the Phase 1 persistence target, but this document stays at the documentation boundary.

## Why Source Adapters Exist

GHG Protocol, DEFRA / DESNZ, and IPCC EFDB have different source formats, publication patterns, file structures, and record shapes.

Source adapters exist so those differences stay isolated instead of being hidden behind one shared parser engine.

Adapters should allow each source family to be discovered, retrieved, parsed, and traced without forcing all sources into one common structure too early.

## Adapter Responsibilities

A source adapter may:

- Discover public source files or source references.
- Retrieve source files when configured and allowed by startup checks.
- Inspect source-family-specific structure.
- Parse source-specific rows, sheets, sections, or records.
- Emit conceptual parser records.
- Emit source traceability references.
- Report unsupported structures.
- Report rejected rows and warnings through explicit handoff boundaries.
- Report normalization notes when parser behavior prepares source values for shared normalization review.

Adapters should preserve source meaning and avoid silently discarding records.

## Adapter Non-Responsibilities

A source adapter should not:

- Define shared validation policy.
- Define shared normalization policy.
- Define reporting behavior.
- Define database schema.
- Persist records directly as a shared storage contract.
- Provide emissions advice.
- Provide legal interpretation.
- Provide audit assurance.
- Provide compliance guarantees.
- Claim official source-owner approval.

Shared validation, normalization, metadata, reporting, and storage concepts should remain outside source-specific adapter logic.

## Conceptual Adapter Lifecycle

A conceptual adapter lifecycle is:

1. Discover source availability or source file structure.
2. Retrieve the source file or accept a configured file reference.
3. Parse source-specific structures.
4. Emit parser records with source traceability.
5. Hand validation inputs to shared validation.
6. Hand normalization notes to shared normalization review.
7. Hand ingestion metadata to shared metadata tracking.
8. Report errors, rejected rows, warnings, and unsupported structures.

The lifecycle describes boundaries only. It does not add a job runner or implementation code.

## Discovery Contract

Discovery should identify source-family-specific structure before parser behavior is finalized.

Discovery output may include:

- Source family.
- Source name.
- Source URL or file reference.
- Publication date or version when available.
- File name, size, content type, and hash when practical.
- Workbook sheets, export sections, or table regions.
- Header rows, column names, and sample rows.
- Candidate master/detail relationships.
- Unsupported or ambiguous structures.

Discovery should not be treated as a completed import.

## Retrieval Contract

Retrieval should obtain public source files or accept configured file references after required startup checks.

Retrieval output should preserve:

- Source family.
- Source name.
- Source URL or file reference.
- Publication date or version when available.
- Retrieval timestamp.
- File name and content type.
- Content hash when practical.
- Raw archive reference when available.

Retrieval should support idempotency by making version and hash information available to shared metadata handling.

## Parse Contract

Parsing should remain source-specific.

Adapters may parse workbook sheets, CSV exports, structured files, or other public source formats into conceptual parser records. Those records should preserve source-specific fields and enough location context to explain where each record came from.

Parser records should include, where available:

- Source family.
- Source name.
- Source file or URL reference.
- Source version or publication date.
- Ingestion run reference.
- Source section, sheet, row, column, or record identifier.
- Source-specific values.
- Parser warnings or unsupported structure notes.

Adapters should not silently discard rows. Rejected rows should be counted and handed off with reasons.

## Validation Handoff

Adapters should hand parser records to shared validation with enough context to evaluate completeness, field interpretation, and source-specific expectations.

Validation handoff should include:

- Parser records.
- Source traceability references.
- Rejected row candidates.
- Parser warnings.
- Unsupported structures.
- Field-level context when available.

The adapter should not hide validation concerns inside source-specific parsing logic when shared validation needs to review them.

## Normalization Handoff

Adapters may prepare source values for normalization, but shared normalization concepts should remain outside the adapter boundary.

Normalization handoff should describe meaningful transformations, such as:

- Trimmed or standardized technical text.
- Parsed dates.
- Parsed numeric values.
- Unit labels detected from source structure.
- Source category or reference mapping notes.

Normalization notes should be explicit and countable. They should preserve enough source context to explain how source values were interpreted.

## Metadata Handoff

Adapters should hand ingestion metadata to shared metadata tracking.

Metadata handoff should include, where available:

- Source family.
- Source name.
- Source URL or file reference.
- Publication date or source version.
- Retrieval timestamp.
- Content hash.
- Parser name.
- Parser version.
- Processing status.
- Counts for discovered, parsed, rejected, warning, and normalization-note records.

Metadata should support repeatable ingestion, source traceability, and operational troubleshooting.

## Error And Warning Expectations

Adapters should report errors and warnings explicitly.

Expected error and warning categories include:

- Source file unavailable.
- Unsupported content type.
- Missing expected sheet, section, header, or column.
- Ambiguous data region.
- Unparseable row or value.
- Unsupported source structure.
- Duplicate source record within the same input.
- Parser behavior that requires downstream validation review.

Errors should explain the affected source family, file reference, source location when available, and reason.

## Source Family Expectations

Phase 1 source adapters should be designed around:

- GHG Protocol.
- DEFRA / DESNZ.
- IPCC EFDB.

Each source family should have its own adapter boundary. Shared helper logic may be introduced later when it removes real duplication without hiding source-specific meaning.

## Python And .NET Parity Expectations

Python is expected first because it is better suited for early source discovery, file handling, spreadsheet inspection, and parser experimentation.

The .NET implementation should aim for behavioral parity later. It should not define a different product scope or source boundary.

Python and .NET implementation paths should remain independent and should not share runtime code.

## Explicit Non-Goals

This source adapter contract does not:

- Define final code contracts or runtime classes.
- Add parser implementation code.
- Add database migrations or SQL schema files.
- Prescribe an ORM.
- Define a shared parser engine.
- Define a final canonical factor table.
- Provide emissions advice.
- Provide legal interpretation.
- Provide audit assurance.
- Provide compliance guarantees.
- Replace source-owner documentation or files.
- Claim official source-owner approval.

## Review Checklist

Before source adapter changes are reviewed, check that they:

- Stay source-family-specific.
- Preserve source traceability back to source family, source name, source URL or file reference, publication date or version, and ingestion run.
- Avoid silently discarding records.
- Report rejected rows, warnings, unsupported structures, and normalization notes explicitly.
- Keep shared validation, normalization, metadata, reporting, and storage concerns outside adapter-specific logic.
- Preserve Python and .NET implementation independence.
- Avoid defining final code contracts or database schema unless a later task explicitly requests it.
- Avoid unsupported legal, accounting, reporting, or source-owner assurance claims.
