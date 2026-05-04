# Normalization Test Coverage Recap

This document recaps the current normalization-related test coverage. It describes what the existing tests protect and what they intentionally leave outside the current artificial normalization boundary.

## Purpose

The normalization package now has contracts, artificial skeletons, usage examples, summary models, and public API exports.

This recap maps the current tests to those boundaries so future tasks can extend coverage without accidentally turning artificial examples into real normalization, persistence, scheduling, or source-specific behavior.

## Current Normalization Test Groups

The current normalization-related tests include:

- `tests/test_parser_normalization_handoff.py`
- `tests/test_parser_normalization_handoff_example.py`
- `tests/test_normalization_contracts.py`
- `tests/test_normalization_contract_example.py`
- `tests/test_normalization_executor.py`
- `tests/test_example_artificial_normalization_executor_usage.py`
- `tests/test_normalization_summary.py`
- `tests/test_example_normalization_result_summary_usage.py`
- `tests/test_normalization_summary_builder.py`
- `tests/test_example_artificial_normalization_summary_builder_usage.py`
- `tests/test_normalization_public_api.py`

These tests focus on deterministic contracts, artificial skeleton behavior, example importability, public API exports, and no hidden file or runtime service requirements.

## Coverage Map

| Test file | Boundary protected | Checks | Intentionally does not verify |
| --- | --- | --- | --- |
| `tests/test_parser_normalization_handoff.py` | Parser-to-normalization handoff model | Empty and populated handoff construction, deterministic entry data, preserved parser records, no file I/O | Parser execution, normalization execution, unit conversion, source-specific mapping |
| `tests/test_parser_normalization_handoff_example.py` | Handoff usage example | Importable deterministic example output, generic artificial records, no runtime service requirements | Real parser output acceptance, real source data, correctness validation |
| `tests/test_normalization_contracts.py` | Normalization contracts | Issue severities, generic normalized records, result summary counts, tuple-based records and issues, frozen dataclasses | Unit conversion, factor meaning, persistence writes |
| `tests/test_normalization_contract_example.py` | Normalization contract usage example | Importable deterministic example output, summary fields, artificial records, warning and error representation | Normalization execution, real data handling, correctness decisions |
| `tests/test_normalization_executor.py` | `ArtificialNormalizationExecutor` skeleton | Handoff input accepted, artificial records returned, deterministic output, empty input behavior, no file I/O | Real normalization behavior, parser behavior changes, source-specific transformations |
| `tests/test_example_artificial_normalization_executor_usage.py` | Artificial executor usage example | Importable deterministic output, artificial records, summary fields, no runtime service requirements | Executor integration with real pipelines, source downloads, persistence |
| `tests/test_normalization_summary.py` | `NormalizationResultSummary` model | Valid construction, non-negative counts, metadata isolation, compatibility aliases, no file I/O | Summary builder behavior, reporting behavior, correctness validation |
| `tests/test_example_normalization_result_summary_usage.py` | Direct summary model usage example | Direct model construction, deterministic artificial fields, no executor use, no runtime service requirements | Summary computation from `NormalizationResult`, aggregation semantics |
| `tests/test_normalization_summary_builder.py` | `ArtificialNormalizationSummaryBuilder` skeleton | Accepts `NormalizationResult`, returns `NormalizationResultSummary`, counts records and issues only, deterministic output, no input mutation, no file I/O | Aggregation beyond output-shape counting, unit conversion, factor interpretation |
| `tests/test_example_artificial_normalization_summary_builder_usage.py` | Artificial summary builder usage example | Direct artificial `NormalizationResult` construction, builder use, deterministic summary fields, no executor use | Executor integration, real source data, parser behavior changes |
| `tests/test_normalization_public_api.py` | Normalization package public exports | Expected public symbols import from package, `__all__` is intentional, internal module names stay internal | Behavior of each exported class or helper beyond import surface |

## What The Tests Intentionally Do Not Cover

The current tests do not cover:

- Real normalization correctness.
- Unit conversion correctness.
- Factor correctness validation.
- Carbon accounting correctness decisions.
- Compliance or legal interpretation.
- External data or source coverage.
- Real source file reading.
- Parser behavior changes.
- Database or persistence behavior.
- Scheduler or retry behavior.
- Downloading or remote access.
- Config loading.

This is intentional. The current normalization layer is artificial, deterministic, and boundary-focused.

## Deferred Test Areas

Future tasks may add tests for later boundaries only when those boundaries are explicitly scoped.

Deferred areas include:

- Real normalization correctness tests.
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

Future normalization test PRs should confirm:

- Tests match the explicitly scoped boundary.
- Artificial examples remain deterministic and in-memory unless a later task scopes otherwise.
- Parser behavior is not changed accidentally.
- Summary tests do not grow beyond output-shape counting unless explicitly scoped.
- No test fixture introduces real source data unless explicitly scoped.
- No test depends on persistence, scheduler, retry, download, remote access, or config loading behavior unless explicitly scoped.
- The local public safety script passes.

## Related Documents

- [Normalization Boundary](normalization-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Normalization Execution Boundary](normalization-execution-boundary.md)
- [Normalization Result Summary Boundary](normalization-result-summary-boundary.md)
- [Normalization Summary Builder Boundary](normalization-summary-builder-boundary.md)
- [Normalization Pipeline Recap](normalization-pipeline-recap.md)
- [Normalization Public API Recap](normalization-public-api-recap.md)
