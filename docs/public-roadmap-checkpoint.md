# Public Roadmap Checkpoint

This checkpoint summarizes the current public repository state after the source adapter, parser, parser-to-normalization handoff, and artificial normalization tracks.

## Purpose

The repository has accumulated a documentation-first architecture track with small artificial contracts, skeletons, examples, and recaps.

This document summarizes what exists today, what does not exist today, and safe future task families. It adds no code, contracts, examples, tests, or runtime behavior.

## Current Public Artifacts

The current public artifacts include:

- Source adapter contracts, local/artificial adapter examples, result summaries, and package recaps.
- Source document contracts and hashing behavior.
- Parser result contracts, artificial parser skeletons, parser usage examples, fixture parser examples, and parser pipeline summaries.
- Parser-to-normalization handoff models, examples, boundary docs, and integration recaps.
- Artificial normalization contracts, executor skeleton, summary model, summary builder skeleton, and usage examples.
- Normalization boundary, recap, public API, test coverage, and deferred implementation roadmap docs.
- Codex-assisted task queue and review workflow documentation.

## What Exists Today

The repository currently has:

- Importable Python contracts for source adapters, parser results, parser handoff, and normalization results.
- Artificial skeletons that demonstrate shape without real source processing.
- Local fixture examples where explicitly documented.
- Deterministic examples and tests for the artificial paths.
- Public documentation maps in `README.md` and `docs/index.md`.
- A local public safety validation script.

These items are intended to make future changes small, reviewable, and boundary-aware.

## What Does Not Exist Today

The repository does not currently include:

- Real source acquisition.
- Real parser-to-normalization integration behavior.
- Real normalization correctness.
- Unit conversion.
- Factor correctness validation.
- Carbon accounting correctness decisions.
- Compliance or legal interpretation.
- Real source data handling.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Runtime config loading.

Current examples remain artificial, deterministic, and in-memory unless an existing local fixture example explicitly documents local fixture discovery.

## Artifact Categories

| Category | Examples | Role |
| --- | --- | --- |
| Documentation-only boundaries and recaps | Source adapter docs, parser boundary docs, normalization recaps, deferred roadmap | Explain scope before behavior changes |
| Contract and model tasks | `SourceDocument`, `ParserResult`, `ParserNormalizationHandoff`, `NormalizationResult` | Define data shape and boundary terms |
| Artificial skeleton tasks | Artificial parsers, `ArtificialNormalizationExecutor`, `ArtificialNormalizationSummaryBuilder` | Demonstrate deterministic behavior without real source processing |
| Artificial usage examples | Source, parser, handoff, normalization, and summary examples | Show importable usage for tests and reviewers |
| Test coverage recaps | Normalization test coverage recap | Describe what tests protect and what they avoid |

## Safe Future Task Families

Future public tasks should continue to use small increments such as:

- Documentation-first boundary tasks.
- Contract or model tasks.
- Artificial skeleton tasks.
- Artificial usage example tasks.
- Public API recap tasks when exports grow.
- Test coverage recap tasks when test boundaries grow.
- Deferred roadmap updates when future task families become clearer.
- Later real implementation tasks only with explicit scope and review gates.

This sequence helps avoid mixing documentation, contract design, skeleton behavior, and real behavior in one change.

## Review Gates Before Real Behavior

Before adding real behavior, reviewers should confirm:

- The task explicitly scopes the real behavior being added.
- Public wording avoids correctness, compliance, or operational-readiness claims.
- Source acquisition, parser behavior, normalization behavior, persistence, and scheduling remain separately scoped.
- Unit conversion and factor correctness have documented boundaries before implementation.
- Real source data is not added unless a task explicitly scopes it.
- Tests remain deterministic and focused on the scoped boundary.
- Public safety validation passes.

## Non-Goals

This checkpoint does not claim:

- Real source acquisition coverage.
- Parser correctness for real external sources.
- Normalization correctness.
- Unit conversion correctness.
- Factor correctness.
- Legal or compliance interpretation.
- Carbon accounting correctness.
- Operational readiness.

It is a public roadmap checkpoint only.

## Deferred Items

The checkpoint intentionally defers:

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

## Related Documents

- [Source Adapter Package Recap](source-adapter-package-recap.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Integration Recap](parser-to-normalization-integration-recap.md)
- [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)
- [Normalization Pipeline Recap](normalization-pipeline-recap.md)
- [Normalization Public API Recap](normalization-public-api-recap.md)
- [Normalization Test Coverage Recap](normalization-test-coverage-recap.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Codex-Assisted Runs](codex-runs/README.md)
