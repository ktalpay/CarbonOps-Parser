# Normalization Public API Recap

This document recaps the current public exports from `carbonfactor_parser.normalization`. It describes the artificial normalization contracts, skeletons, and helpers that exist today without adding new code or runtime behavior.

## Purpose

The normalization package now exposes enough names that a compact public API map helps reviewers and future tasks understand what each item is for.

This recap describes exported names at a high level. It does not change the public API, add contracts, or introduce new examples.

## Current Exported Normalization API

The package currently exports:

- `NormalizationIssue`
- `NormalizationIssueSeverity`
- `NormalizationResult`
- `NormalizationResultSummary`
- `NormalizedRecord`
- `ArtificialNormalizationExecutor`
- `ArtificialNormalizationSummaryBuilder`
- `ParserNormalizationHandoff`
- `ParserNormalizationHandoffEntry`
- `build_parser_normalization_handoff`

These exports support artificial, deterministic normalization boundary examples. They do not imply real source coverage, unit conversion, factor correctness, legal or compliance interpretation, or production readiness.

## API Role Table

| Public name | Purpose | Boundary role | Does not claim | Kind |
| --- | --- | --- | --- | --- |
| `NormalizationIssueSeverity` | Names normalization issue severities | Normalization contract vocabulary | Issue prioritization beyond warning and error | Contract enum |
| `NormalizationIssue` | Carries normalization-level warning or error details | Normalization result issue model | Legal, compliance, or factor correctness meaning | Contract model |
| `NormalizedRecord` | Carries generic normalized record shape | Normalization output model | Real factor value acceptance or unit conversion correctness | Contract model |
| `NormalizationResult` | Groups normalized records and normalization issues | Normalization output boundary | Persistence, scheduling, or external source handling | Contract model |
| `NormalizationResultSummary` | Describes output-shape summary counts and artificial metadata | Summary model boundary | Correctness validation or reporting-engine behavior | Contract model |
| `ParserNormalizationHandoffEntry` | Describes one parser record prepared for normalization handoff | Parser-to-normalization bridge | Parser execution or normalization execution | Contract model |
| `ParserNormalizationHandoff` | Groups parser handoff entries and issue counts | Parser-to-normalization boundary | Automatic acceptance of parser records as normalized output | Contract model |
| `build_parser_normalization_handoff` | Builds handoff metadata from an existing parser result | Handoff model helper | Normalization execution, unit conversion, or factor interpretation | Usage-facing support |
| `ArtificialNormalizationExecutor` | Maps handoff entries into artificial normalized records | Artificial execution skeleton | Real normalization correctness or source-specific behavior | Artificial skeleton |
| `ArtificialNormalizationSummaryBuilder` | Counts records and issues from an existing normalization result | Artificial summary skeleton | Aggregation beyond output-shape counting | Artificial skeleton |

## Boundary Relationships

`ParserNormalizationHandoff` and `ParserNormalizationHandoffEntry` sit at the parser-to-normalization boundary.

`ArtificialNormalizationExecutor` accepts handoff input and produces artificial `NormalizationResult` output.

`NormalizationResult` contains `NormalizedRecord` objects and `NormalizationIssue` entries.

`NormalizationResultSummary` describes output shape only.

`ArtificialNormalizationSummaryBuilder` converts an existing `NormalizationResult` into `NormalizationResultSummary` by counting records and issues only.

These relationships are intentionally narrow and deterministic. They do not connect to file readers, source downloaders, databases, schedulers, or config loaders.

## Non-Goals

The normalization public API recap does not introduce:

- Real normalization correctness.
- Unit conversion.
- Factor correctness validation.
- Carbon accounting correctness decisions.
- Compliance or legal interpretation.
- Real source data handling.
- File reading.
- Parser behavior changes.
- Database or persistence behavior.
- Scheduler or retry behavior.
- Remote source access or downloading.
- Config loading.

## Deferred Items

The normalization public API intentionally defers:

- Real normalization correctness.
- Executor integration beyond current artificial skeleton behavior.
- Aggregation semantics beyond output-shape counting.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Real source data.
- File reading.
- Parser behavior change.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Config loading.

## Review Checklist

Future normalization public API PRs should confirm:

- New public exports are intentionally scoped and documented.
- Existing public exports remain stable unless a task explicitly scopes a change.
- Artificial skeletons remain artificial and deterministic.
- Parser behavior is not changed accidentally.
- No output is described as correctness validation.
- No real source data is added unless explicitly scoped.
- No persistence, scheduler, retry, download, remote access, or config loading behavior is introduced.
- The local public safety script passes.

## Related Documents

- [Normalization Boundary](normalization-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Normalization Execution Boundary](normalization-execution-boundary.md)
- [Normalization Result Summary Boundary](normalization-result-summary-boundary.md)
- [Normalization Summary Builder Boundary](normalization-summary-builder-boundary.md)
- [Normalization Pipeline Recap](normalization-pipeline-recap.md)
