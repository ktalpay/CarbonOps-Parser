# Normalization Deferred Implementation Roadmap

This roadmap consolidates deferred normalization implementation areas and proposes a conservative sequencing model for future work.

## Purpose

The normalization track currently has artificial contracts, skeletons, examples, and documentation recaps. Those artifacts define boundaries and deterministic shapes before real normalization behavior is introduced.

This document gathers the deferred areas from the normalization boundary, execution, summary, pipeline, public API, and test coverage docs. It also describes safe task families for future work.

## Current Normalization Baseline

The current baseline includes:

- Parser-to-normalization handoff models.
- Source-agnostic normalization contracts.
- `ArtificialNormalizationExecutor`.
- Artificial executor usage examples.
- `NormalizationResultSummary`.
- Direct summary model usage examples.
- `ArtificialNormalizationSummaryBuilder`.
- Artificial summary builder usage examples.
- Public API and test coverage recaps.

These capabilities are artificial, deterministic, local, and in-memory. They demonstrate contract shape and boundary behavior only.

## Deferred Implementation Areas

The normalization track intentionally defers:

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

Each deferred area should remain outside small artificial tasks unless a later task explicitly scopes it.

## Suggested Future Sequencing

Future normalization work should continue to use small, reviewable tasks. A conservative sequence for any new area is:

1. Documentation-first boundary task.
2. Contract or model task.
3. Artificial skeleton task.
4. Artificial usage example task.
5. Focused tests for deterministic artificial behavior.
6. Recap or public API documentation if the surface area grows.
7. Later real implementation tasks only with explicit scope.

This sequence mirrors the current repository style: document the boundary first, add narrow contracts, add artificial behavior, prove deterministic usage, and defer real behavior until it is deliberately scoped.

## Safe Future Task Families

Potential future task families include:

- Normalization validation boundary documentation.
- Artificial normalization validation contract models.
- Artificial validation skeletons that inspect shape only.
- Persistence boundary documentation.
- Parser-to-normalization integration boundary documentation.
- Source-specific normalization boundary documentation.
- Real source normalization planning docs before any source-specific implementation.

These task families should keep real data handling, unit conversion, correctness decisions, persistence, scheduling, and remote access separate unless explicitly scoped.

## Review Gates

Before real behavior is added, reviewers should confirm:

- The task explicitly scopes the new behavior.
- Public wording avoids correctness, compliance, or production-readiness claims.
- Test fixtures do not introduce real source data unless explicitly scoped.
- Unit conversion has a documented boundary before implementation.
- Factor correctness has a documented boundary before implementation.
- Persistence and scheduler behavior remain outside normalization unless separately scoped.
- Parser behavior is not changed accidentally.
- Public safety validation passes.
- New tests are deterministic and focused on the scoped boundary.

## Intentionally Out Of Scope

This roadmap does not add:

- Code.
- Contracts.
- Examples.
- Tests.
- Real normalization behavior.
- Unit conversion.
- Factor correctness logic.
- Parser behavior changes.
- Database or persistence behavior.
- Scheduler or retry behavior.
- Remote source access or downloading.
- Config loading.

## Non-Goals

This roadmap does not claim:

- Real factor correctness.
- Unit conversion correctness.
- Legal or compliance interpretation.
- Carbon accounting correctness.
- Production readiness.
- External data or source coverage.

It is a planning document for future task sequencing only.

## Related Documents

- [Normalization Boundary](normalization-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Normalization Execution Boundary](normalization-execution-boundary.md)
- [Normalization Result Summary Boundary](normalization-result-summary-boundary.md)
- [Normalization Summary Builder Boundary](normalization-summary-builder-boundary.md)
- [Normalization Pipeline Recap](normalization-pipeline-recap.md)
- [Normalization Public API Recap](normalization-public-api-recap.md)
- [Normalization Test Coverage Recap](normalization-test-coverage-recap.md)
