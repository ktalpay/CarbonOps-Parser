# Engineering Standards

CarbonOps-Parser is a documentation-first reference project for scheduled carbon factor ingestion and source-aware parsing. These standards describe how changes should be shaped, reviewed, and documented.

## Purpose

The purpose of this document is to keep repository changes consistent, reviewable, and aligned with the Phase 1 scope.

Engineering work should favor:

- Small, testable increments.
- Clear source boundaries.
- Parser correctness over framework complexity.
- Deterministic behavior where practical.
- Explicit validation errors.
- Conservative public wording.

## Repository Principles

CarbonOps-Parser contains two independent implementation options:

- `src/python`
- `src/dotnet`

The Python and .NET implementations should follow the same conceptual ingestion workflow, but they should not depend on each other.

Shared documentation, examples, configuration models, and database schema notes should describe the cross-language contract. Runtime implementation details should stay within the relevant implementation path.

Phase 1 should remain focused on scheduled source ingestion, raw file archiving, source-specific parsing, validation, and PostgreSQL-backed ingestion metadata.

## Change Management Expectations

Changes should be small enough to review in one pass.

Each change should have a clear purpose, such as documentation baseline work, schema documentation, source discovery, parser mapping, validation behavior, or implementation-specific service wiring.

Contributors should avoid combining unrelated work in one change. Documentation updates, schema changes, parser behavior, and service runtime changes should be split when practical.

Changes should preserve existing repository structure unless the change explicitly improves clarity or removes duplication.

## Coding Standards

Use the existing language, framework, and folder conventions of the implementation being changed.

Prefer standard-library functionality unless an external dependency is clearly justified by source format handling, parser correctness, maintainability, or safety. New dependencies should be documented with their purpose and expected scope.

Parser code should prioritize accurate source interpretation, explicit validation, and traceable import behavior over broad abstractions.

Where practical, behavior should be deterministic:

- Stable ordering for parsed records and validation output.
- Repeatable hashing and version checks.
- Predictable file archive paths.
- Clear handling of missing, empty, malformed, or unexpected source fields.

Errors should be explicit and actionable. Validation failures should identify the source family, input location when available, affected field, and reason for rejection or warning.

## Testing Expectations

Tests should scale with change risk.

Documentation-only changes should be inspected for broken links, inconsistent terminology, and unsupported claims.

Parser and validation changes should include focused tests for expected rows, edge cases, malformed values, and source-specific mapping behavior.

Database changes should include checks for schema availability, table creation order, idempotency, and provider validation where practical.

Scheduling and background service changes should cover source enablement, schedule interpretation, skip behavior for unchanged source hashes, and startup ordering.

## Documentation Expectations

Documentation should be updated with the code or schema behavior it describes.

Repository documentation should:

- Make source boundaries clear.
- Separate shared concepts from Python-specific and .NET-specific details.
- Describe unsupported providers and source limitations plainly.
- Avoid confidential, proprietary, or non-public source data.
- Avoid compliance, legal, accounting, certification, or reporting assurance claims.

Examples should use public source names, generic configuration values, and safe placeholder paths.

## Review Checklist

Before review, check that the change:

- Matches the stated task scope.
- Keeps Python and .NET implementation paths independent.
- Preserves the critical startup rule that source documents are not downloaded, parsed, or imported before the database schema is available.
- Uses source-specific table and parser boundaries.
- Provides explicit validation behavior for parser-facing changes.
- Avoids unnecessary dependencies.
- Updates documentation links when new documents are added.
- Avoids unsupported public claims.
- Does not include confidential or proprietary source data.

## Explicit Non-Goals

These standards do not define a carbon accounting methodology.

They do not provide compliance, legal, accounting, certification, reporting, or source-data correctness assurance.

They do not define deployment hardening, service-level guarantees, or a general-purpose data platform.

They do not require Python and .NET to share runtime code or implementation dependencies.

They do not require Phase 1 to normalize all source families into one canonical factor table.
