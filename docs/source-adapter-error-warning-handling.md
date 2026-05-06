# Source Adapter Error And Warning Handling

Source adapter warnings and errors describe adapter-level discovery or execution handoff issues. They do not represent emissions result correctness, parser validation, persistence status, scheduling status, or external framework status.

## Purpose

This document explains how source adapter code and future adapter execution layers should use warnings and errors.

Discovery warnings currently appear on `AdapterDiscoveryResult`. Later parse execution handoff warnings and errors may be represented on `SourceAdapterExecutionResult`.

## Warning Vs Error Guidance

A warning means the adapter can complete the current discovery or handoff step, but it encountered a non-fatal issue.

An error means the adapter or execution layer could not complete the selected source/configuration step.

Guidance:

- Missing optional local directory: may return an empty discovery result with a warning when the adapter contract already behaves that way.
- Empty directory: should usually be an empty discovery result without error; a warning may be useful if the caller expected files.
- Invalid adapter configuration: should be treated as an error by the caller or future execution layer.
- Unsupported source family or key: should be handled by `SourceAdapterRegistry.get()` lookup behavior, not by adapter discovery.
- Warnings should not be treated as failure by default.
- Zero discovered documents should not always be treated as failure.

## Suggested Examples

| Scenario | Suggested handling |
| --- | --- |
| Missing directory | Empty discovery result with warning when local discovery is optional |
| Empty directory | Empty discovery result; optional warning if configured source expected files |
| Unsupported extension filter | Warning or caller-side configuration error, depending on whether discovery can continue |
| Permission denied | Error when files cannot be listed for the selected directory |
| Malformed local path | Error or controlled empty result, depending on adapter configuration expectations |
| Source unavailable in future remote adapter | Error when discovery cannot complete |
| Partial discovery in future remote adapter | Warning when some source references were discovered and some were skipped |

## Responsibility Boundaries

| Area | Owns |
| --- | --- |
| Source adapter discovery issues | Missing local paths, skipped files, unsupported source references, discovery warnings |
| Parser validation issues | Record shape, missing fields, malformed values, parser-specific rejection reasons |
| Normalization issues | Value transformation notes, unit/date interpretation notes, source-specific normalization concerns |
| Persistence issues | Database availability, write failures, transaction outcomes, storage metadata |
| Scheduler and retry issues | Run timing, retry policy, cancellation, backoff, source enablement |
| Legal or compliance interpretation | Out of scope for the adapter package |

## Consumer Guidance

Callers should inspect:

- Discovered `SourceDocument` entries from `AdapterDiscoveryResult.documents`.
- Discovery warnings from `AdapterDiscoveryResult.warnings`.
- Execution handoff warnings from `SourceAdapterExecutionResult.warnings`.
- Execution handoff errors from `SourceAdapterExecutionResult.errors`.

For examples and future ingestion boundaries, `summarize_source_adapter_result()` can convert an `AdapterDiscoveryResult` or `SourceAdapterExecutionResult` into compact counts and deterministic source metadata. It is a lightweight helper, not a broader output layer.

See [examples/source_adapter_summary_example.py](../examples/source_adapter_summary_example.py) for a deterministic local fixture example.

The current `SourceAdapterExecutionResult` contract does not include a separate success or failure status field. Consumers should inspect `errors` directly, or use `has_errors(result)` when working with execution result values.

Consumers should not assume:

- Any warning means failure.
- Zero discovered documents means failure.
- Missing warnings means source contents are valid.
- Missing errors means parser validation, persistence, or scheduled execution has completed.

## Non-Goals

This guidance does not define:

- Retry policy.
- Persistence logging.
- Exception taxonomy.
- Source-specific correctness determinations.
- Parser coupling.
- Scheduler or cancellation behavior.

## Future Extension Points

Future tasks may add:

- Structured issue codes if string messages become hard to review.
- Source-specific diagnostic metadata when needed for traceability.
- Retry policy outside the adapter package.
- Persistence logging outside the adapter package.

Any extension should keep discovery concerns separate from parser validation, normalization, persistence, and scheduling boundaries.
