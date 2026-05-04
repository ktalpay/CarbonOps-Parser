# Repository Navigation Guide

This guide helps readers choose where to start in the CarbonOps-Parser documentation.

## Purpose

The repository now has many boundary, recap, example, and roadmap documents. This guide groups the existing documents by reader goal so reviewers and contributors can find the right path quickly.

This guide references existing documents only. It adds no code, contracts, examples, tests, or runtime behavior.

## Start Here

For a high-level orientation, start with:

1. [Architecture](architecture.md)
2. [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
3. [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)
4. [Roadmap](roadmap.md)
5. [Task Breakdown](task-breakdown.md)

For the current public-safety and boundary posture, also read:

- [Public Safety](public-safety.md)
- [Limitations](limitations.md)

## Reading Paths

### Architecture Overview Path

- [Architecture](architecture.md)
- [Configuration Model](configuration-model.md)
- [Source Support](source-support.md)
- [Source Discovery](source-discovery.md)
- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)

Use this path to understand the repository shape before reading implementation-specific boundary docs.

### Source Adapter Path

- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
- [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md)
- [Source-Specific Adapter Skeleton Guidance](source-specific-adapter-skeleton-guidance.md)
- [Source Adapter Package Recap](source-adapter-package-recap.md)

Use this path to understand source discovery, `SourceDocument` references, adapter summaries, and source-specific adapter boundaries.

### Parser Path

- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Source-Specific Parser Skeleton Boundaries](source-specific-parser-skeleton-boundaries.md)
- [Real Format Parser Boundary](real-format-parser-boundary.md)

Use this path to understand parser result contracts, artificial parser skeletons, and the difference between parser output and later normalization.

### Parser-To-Normalization Handoff Path

- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Parser To Normalization Integration Recap](parser-to-normalization-integration-recap.md)
- [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)

Use this path to understand how parser output moves toward normalization through `ParserNormalizationHandoff` without merging parser execution and normalization execution.

### Normalization Path

- [Normalization Boundary](normalization-boundary.md)
- [Normalization Execution Boundary](normalization-execution-boundary.md)
- [Normalization Result Summary Boundary](normalization-result-summary-boundary.md)
- [Normalization Summary Builder Boundary](normalization-summary-builder-boundary.md)
- [Normalization Pipeline Recap](normalization-pipeline-recap.md)
- [Normalization Public API Recap](normalization-public-api-recap.md)

Use this path to understand the artificial normalization executor, normalization contracts, summary model, and summary builder skeleton.

### Testing And Review Path

- [Engineering Standards](engineering-standards.md)
- [Normalization Test Coverage Recap](normalization-test-coverage-recap.md)
- [Codex-Assisted Runs](codex-runs/README.md)
- [Codex Reviewer Checklist](codex-runs/reviewer-checklist.md)
- [Local Public Safety Validation](codex-runs/local-public-safety-validation.md)

Use this path to understand deterministic test expectations, review boundaries, and public-safety checks.

### Roadmap And Deferred Work Path

- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Roadmap](roadmap.md)
- [Task Breakdown](task-breakdown.md)
- [Codex Task Queue](codex-runs/task-queue.md)

Use this path to understand what is intentionally deferred and how future work should remain small and reviewable.

## Current Documentation Map

For a complete flat list of current docs, use [Documentation Index](index.md).

The README documentation map also links the main public-facing docs from the repository root.

## What This Guide Does Not Claim

This guide does not claim:

- Real source acquisition coverage.
- Parser correctness for real external sources.
- Normalization correctness.
- Unit conversion correctness.
- Factor correctness.
- Legal or compliance interpretation.
- Carbon accounting correctness.
- Operational readiness.

It only helps readers navigate existing documentation.

## Deferred Areas

The repository navigation guide intentionally leaves these areas deferred:

- Real source acquisition.
- Real parser-to-normalization integration behavior.
- Real normalization correctness.
- Executor integration beyond current artificial skeleton behavior.
- Aggregation semantics beyond output-shape counting.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Real source data.
- File reading beyond existing local and artificial examples.
- Source adapter behavior change.
- Parser behavior change.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Config loading.

## Review Checklist

Future navigation guide updates should confirm:

- Links point to existing documents.
- Reading paths remain goal-oriented rather than exhaustive.
- New docs are added to the guide only when they help readers choose a path.
- The guide does not imply real source coverage, parser correctness, normalization correctness, or operational readiness.
- No code, contracts, examples, or tests are added in navigation-only tasks.
- The local public safety script passes.
