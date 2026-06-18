# Ingestion Metadata Model

CarbonOps-Parser uses ingestion metadata concepts to describe how source retrieval, parsing, validation, and persistence should be tracked. This document is conceptual documentation only.

## Purpose

The purpose of the ingestion metadata model is to keep ingestion runs repeatable, traceable, reviewable, and easier to troubleshoot.

Metadata should explain what source was processed, which parser handled it, what happened during processing, and whether records were parsed, rejected, or completed with warnings.

## Scope

This document defines the intended metadata boundary for Phase 1 design discussions.

It does not define a final database schema, add migrations, prescribe an ORM, or implement runtime behavior.

Phase 1 persistence targets PostgreSQL, but this document stays at the model and documentation boundary.

## Why Ingestion Metadata Exists

Ingestion metadata exists to support:

- Repeatable ingestion.
- Source traceability.
- Validation review.
- Operational troubleshooting.
- Idempotency decisions.
- Later persistence design.

Metadata should connect source discovery, raw file retrieval, parser output, validation summaries, and processing status without replacing source-specific master/detail records.

## Conceptual Metadata Fields

The conceptual metadata model should include:

| Field | Purpose |
| --- | --- |
| `ingestion_id` | Stable identifier for one ingestion run or attempt. |
| `source_family` | Source family, such as GHG Protocol, DEFRA / DESNZ, or IPCC EFDB. |
| `source_name` | Specific configured source name or source package name. |
| `source_url` | Public source URL when retrieval uses a URL. |
| `file_reference` | Local archive path, configured file reference, or source file identifier. |
| `source_version` | Source version key when available. |
| `publication_date` | Source publication date when available. |
| `retrieved_at` | Timestamp when the source file was retrieved or accepted for processing. |
| `content_hash` | Hash of the retrieved or referenced source content when practical. |
| `parser_name` | Name of the parser used for the source family or file type. |
| `parser_version` | Version or identifier for the parser behavior used during the run. |
| `processing_status` | Current or final processing state. |
| `records_discovered` | Count of candidate records discovered before parsing or validation. |
| `records_parsed` | Count of records parsed into source-specific structures. |
| `records_rejected` | Count of records rejected by parsing or validation. |
| `validation_issue_count` | Count of validation issues recorded for the run. |
| `normalization_note_count` | Count of normalization notes recorded for the run. |
| `failure_reason` | Short failure reason when processing fails or is cancelled. |
| `created_at` | Timestamp when metadata for the run was created. |
| `updated_at` | Timestamp when metadata for the run was last updated. |

Field names are conceptual. They may be refined when persistence design is implemented.

## Processing Status Model

Processing status should describe the lifecycle of an ingestion run.

Conceptual states include:

- `discovered`: Source or source file candidate was identified.
- `retrieved`: Source file was retrieved or accepted from a configured file reference.
- `parsed`: Parser produced source-specific parsed records.
- `validated`: Validation completed and produced accepted records, warnings, or rejections.
- `completed`: Processing completed without recorded warnings or failures.
- `completed_with_warnings`: Processing completed with validation issues or normalization notes that should be reviewed.
- `failed`: Processing stopped because of an error.
- `cancelled`: Processing was intentionally stopped before completion.

Status values should be stable enough for review and troubleshooting, but this document does not define a job runner.

## Validation Summary Boundary

Validation summaries should count parser and validation outcomes without hiding detail.

At minimum, metadata should support counts for:

- Records discovered.
- Records parsed.
- Records rejected.
- Validation issues.
- Normalization notes.

Detailed validation issues should remain separately reviewable. Summary counts should help readers decide whether to inspect detailed issues, not replace those details.

The parser should avoid silent data loss. Rejections, warnings, and normalization notes should be countable and reviewable.

## Failure And Retry Boundary

Failure metadata should identify why processing stopped and which source, file reference, parser, and ingestion run were affected.

Retry behavior may be documented conceptually with statuses, hashes, timestamps, and failure reasons. This task does not add retry code, cancellation code, or background job runner behavior.

A later implementation may use metadata to decide whether a failed run can be retried safely.

## Idempotency Expectations

Metadata should support idempotency by tracking source version, publication date, file reference, content hash, parser version, and processing status.

If a source version and content hash are unchanged, ingestion should be able to skip duplicate processing when that policy is selected.

If parser behavior changes, the parser version should make it possible to distinguish a new processing attempt from a duplicate source file.

## Source Traceability Expectations

Source traceability is mandatory.

Parsed records should remain explainable back to:

- Source family.
- Source name.
- Source URL or file reference.
- Source version or publication date when available.
- Raw content hash when practical.
- Ingestion run.
- Parser name and parser version.

Normalization should preserve enough information to explain how source values were interpreted. Meaningful transformations should have validation issues or normalization notes.

## Storage Boundary

Metadata should describe ingestion lifecycle and processing outcomes.

It should not replace:

- Raw files in the configured archive path.
- Source-specific master/detail records.
- Detailed validation issue records.
- Source discovery notes or parser mapping documentation.

The intended architecture is shared ingestion metadata plus source-specific storage. This task does not create migrations, SQL schema files, ORM models, or implementation classes.

## Python And .NET Implementation Expectations

Python implements the first ingestion metadata behavior because it is the active runtime path for source discovery, file handling, parser experimentation, and the current operator-run ingestion workflow.

The .NET implementation should aim for conceptual parity later. It should use language-appropriate structure while preserving the same metadata concepts and source traceability expectations.

The two implementation paths should remain independent and should not share runtime code.

## Explicit Non-Goals

This metadata model does not:

- Define a final database schema.
- Add migrations or implementation classes.
- Prescribe a specific ORM.
- Provide emissions advice.
- Provide legal interpretation.
- Provide audit assurance.
- Provide compliance guarantees.
- Guarantee source data correctness.
- Replace source-owner documentation or files.
- Define a universal calculation model.

## Review Checklist

Before ingestion metadata changes are reviewed, check that they:

- Stay at the requested documentation or implementation boundary.
- Preserve source traceability back to the source family, file reference, and ingestion run.
- Avoid silent data loss by tracking rejected records, validation issues, and normalization notes.
- Keep summary counts separate from detailed validation records.
- Support idempotency decisions through version, publication date, hash, parser version, and status concepts.
- Avoid adding schema, migration, ORM, or job runner behavior unless the task explicitly requests it.
- Preserve Python and .NET implementation independence.
- Avoid unsupported legal, accounting, reporting, or source-owner assurance claims.
