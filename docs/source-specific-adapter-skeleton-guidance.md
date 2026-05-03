# Source-Specific Adapter Skeleton Guidance

Source-specific adapter skeletons should make source discovery boundaries explicit before parser, runtime, or storage behavior exists. They should initially discover and describe candidate source documents only.

## Purpose

This guidance exists to keep future source-specific adapters small, testable, and isolated.

A source-specific skeleton may capture source family naming, local discovery rules, and source document traceability. It should not parse factors, normalize values, persist records, schedule work, download files, or interpret compliance status.

## When To Add A Source-Specific Adapter Skeleton

Add a source-specific skeleton only when at least one of these conditions is true:

- Repeated source-specific discovery rules need a stable home.
- Source family, source name, or source key conventions need to be explicit.
- Fixture-based or static local examples are no longer enough to describe expected discovery behavior.
- Parser and ingestion logic can remain outside the adapter task.

If the change requires parsing, downloading, persistence, scheduling, or runtime orchestration, split that work behind a separate boundary.

## Skeleton Responsibilities

A skeleton may:

- Identify a source family, source name, or project-level source key.
- Discover candidate local files or use pre-supplied document references.
- Apply extension or file naming filters.
- Return `SourceDocument` entries with traceability metadata available at discovery time.
- Return discovery warnings through `AdapterDiscoveryResult`.
- Preserve warning or error handoff boundaries for later `SourceAdapterExecutionResult` usage.
- Remain deterministic in unit tests.

Skeletons should avoid hiding source-specific behavior inside shared helpers or the registry.

## Explicit Non-Responsibilities

Skeletons must not:

- Download files.
- Perform remote authentication.
- Parse emissions factors.
- Normalize factor values.
- Write to databases.
- Schedule jobs.
- Implement retry or cancellation orchestration.
- Certify correctness or compliance.

## Naming Conventions

Prefer names that make the source boundary visible without implying parser behavior.

Examples:

- `src/carbonfactor_parser/source_adapters/<source_name>_adapter.py`
- `<SourceName>SourceAdapter`
- `tests/test_<source_name>_source_adapter.py`

Use existing project style when it conflicts with these examples. Avoid names that imply full ingestion, downloader, parser, or persistence behavior unless that behavior is explicitly added by a later task.

## Test Expectations

Source-specific skeleton tests should cover:

- Deterministic discovery ordering.
- Missing or empty input handling.
- Warning behavior for non-fatal discovery issues.
- Error handoff expectations when a later execution result boundary is involved.
- Extension or name filtering.
- Registry compatibility when the adapter is exported or used in examples.
- No parsing or content interpretation.

Tests should use artificial local fixtures unless a later task explicitly approves a different source boundary.

`ExampleSourceAdapter` provides an artificial local skeleton that demonstrates this pattern without representing a real source.

## Documentation Expectations

Skeleton PRs should document:

- The source-specific discovery boundary.
- The source family, source name, or source key conventions introduced.
- Deferred runtime concerns such as parser selection, persistence, scheduling, retry behavior, and downloads.

Related boundary docs:

- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
- [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md)

## Review Checklist

Before approving a source-specific adapter skeleton PR, reviewers should confirm:

- The change adds no parser, downloader, persistence, scheduler, or retry behavior.
- Source-specific logic is isolated to the adapter skeleton.
- Discovery output is deterministic and covered by tests.
- `SourceDocument` traceability fields are populated as far as the skeleton can support.
- Warnings or errors are explicit and do not silently discard candidate records.
- Registry changes are explicit and do not add auto-discovery.
- Public exports are intentional if the adapter is exported.
- Documentation links describe deferred runtime concerns.
- The PR makes no readiness, correctness, or compliance claims.

## Flow Diagram

```mermaid
flowchart LR
    skeleton["Source-specific adapter skeleton"]
    discovery["AdapterDiscoveryResult"]
    documents["SourceDocument entries"]
    future["Future parser or ingestion boundary"]

    skeleton -->|"discover()"| discovery
    discovery --> documents
    documents --> future
```

## Future Extension Points

Future tasks may add:

- Source-specific parser slices after source structure review.
- Runtime configuration boundaries outside adapter construction.
- Download behavior behind a separate source retrieval boundary.
- Persistence integration behind a separate ingestion boundary.
- Scheduler or retry behavior outside the adapter package.

Each extension should keep source discovery, parsing, normalization, persistence, and runtime orchestration as separate reviewable changes.
