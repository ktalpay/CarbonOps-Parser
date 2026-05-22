# Production Readiness Gap Analysis

This document records the historical gap between the early public
CarbonOps-Parser artifact and a future implementation that could be reviewed for
production use. PROD-002 supersedes any project-level production-ready reading:
the Python runtime now has a production operator path, the .NET runtime is not
production-ready yet, and project-level production-ready is blocked until both
runtimes pass the production parity contract.

It adds no code, contracts, examples, tests, runtime behavior, source acquisition, persistence, scheduling, configuration loading, unit conversion, factor correctness logic, or deployment workflow.

## Purpose

The current repository is not project-level production-ready.

This gap analysis gives reviewers and contributors a conservative map of what is missing before any Python or .NET implementation can be considered for production use. It keeps current documentation-first work separate from future implementation tasks.

The existing artificial examples and skeletons do not prove real-world correctness. Existing smoke tests protect import/export and documentation governance only. Production readiness requires explicit future implementation tasks with narrow scope, tests, and review gates.

## Current Baseline

The current public artifact baseline includes:

- Source adapter contracts, local/artificial adapter examples, result summaries, and package recaps.
- Parser result contracts, artificial parser skeletons, parser usage examples, fixture parser examples, and parser pipeline summaries.
- Parser-to-normalization handoff models, examples, boundary docs, and integration recaps.
- Artificial normalization contracts, executor skeleton, summary model, summary builder skeleton, and usage examples.
- Documentation recaps, checkpoints, review checklists, and navigation maps.
- Governance smoke tests for documentation map references, related-document references, task queue consistency, and public API exports.

These artifacts are useful for scope control, reviewability, and future implementation planning. They do not establish real source coverage, parser correctness, normalization correctness, factor correctness, carbon accounting correctness, operational readiness, or deployment readiness.

## Python Production Readiness Gaps

The Python path still needs explicitly scoped future work for:

- Runtime source adapter behavior beyond current artificial and local examples.
- Real parser behavior for source-specific formats.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Unit conversion boundaries and implementation.
- Factor correctness boundaries and implementation.
- File I/O beyond current local/artificial examples.
- Configuration loading.
- Persistence and database behavior.
- Scheduler, retry, and cancel behavior.
- Downloading or remote source access.
- Error handling across runtime boundaries.
- Public API hardening beyond current export smoke tests.
- Packaging and release workflow.

Python production hardening should remain deferred until boundary documents and focused implementation tasks define the exact behavior under review.

## .NET Production Readiness Gaps

The .NET path is currently a planned implementation option rather than a parity implementation.

The .NET path still needs explicitly scoped future work for:

- .NET project structure and runtime entry points.
- Contract parity with the Python source adapter, parser, handoff, and normalization concepts.
- Source adapter behavior.
- Parser behavior.
- Parser-to-normalization handoff behavior.
- Normalization behavior.
- Persistence/config/scheduler boundaries and implementation.
- Test strategy that can be compared against Python behavior without assuming undocumented parity.
- Packaging and release workflow.

.NET parity should begin with design and contract validation before implementation. Cross-language contract validation remains deferred until both implementation paths have stable, reviewed surfaces.

## Shared Runtime/Operational Gaps

Shared production readiness gaps include:

- Operational hardening for long-running runs, failure modes, backoff policy, cancellation, idempotency, and recovery.
- Data/source acquisition boundaries for source discovery, source version detection, downloads, archive layout, and provenance records.
- Parser correctness boundaries for real file structures, schema drift, unsupported rows, validation issues, and reviewer-visible assumptions.
- Normalization/unit conversion/factor correctness boundaries before any real conversion or factor validation logic is added.
- Persistence/config/scheduler boundaries before database writes, config loading, job orchestration, retry, or cancel behavior is added.
- Observability/logging/metrics boundaries for runtime events, diagnostics, failure summaries, and supportable operations.
- Packaging/deployment/release boundaries for installable artifacts, release notes, versioning, compatibility, and upgrade behavior.
- Security/secrets/configuration boundaries for sensitive configuration, local development defaults, and runtime credential handling.

Each area should be introduced through small future tasks. None should be bundled into this documentation-only task.

## Testing Gaps

Current smoke tests are intentionally narrow. They protect documentation governance and selected public import/export surfaces only.

Testing gaps include:

- Real source acquisition tests.
- Real parser correctness tests.
- Parser-to-normalization integration tests.
- Normalization runtime tests.
- Unit conversion tests.
- Factor correctness tests.
- Persistence and database tests.
- Configuration loading tests.
- Scheduler, retry, and cancel tests.
- Observability/logging/metrics tests.
- Security/secrets handling tests.
- Packaging and deployment tests.
- Cross-language contract validation tests.

Future tests should stay deterministic, local where possible, and tied to narrowly scoped implementation tasks.

## Safe Future Sequencing

A safe documentation-first sequence is:

1. Production readiness boundary docs.
2. Source acquisition boundary docs.
3. Persistence/config boundary docs.
4. Scheduler/retry boundary docs.
5. Python implementation hardening.
6. .NET parity design.
7. .NET implementation.
8. Integration tests.
9. Observability/release packaging.
10. Final production readiness review.

This sequence should remain flexible, but future tasks should keep boundaries, implementation, tests, and release decisions reviewable as separate changes.

## Non-Goals

This document does not add or claim:

- Real source acquisition.
- Real parser correctness.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Real source data handling.
- File I/O beyond current local/artificial examples.
- Config loading.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Observability, logging, or metrics.
- Security/secrets handling.
- Packaging or deployment.
- Python production hardening.
- .NET parity implementation.
- Cross-language contract validation.

## Review Checklist

Reviewers should confirm:

- The change is documentation-only.
- The repository is described as not ready for production use.
- Existing artificial examples and skeletons are not presented as proof of real-world correctness.
- Existing smoke tests are described as import/export and documentation governance checks only.
- Future production readiness is tied to explicit implementation tasks, narrow scope, tests, and review gates.
- Real source acquisition remains deferred.
- Parser correctness remains deferred.
- Unit conversion and factor correctness remain deferred.
- Carbon accounting correctness and compliance/legal interpretation remain deferred.
- Persistence, config loading, scheduler, retry/cancel, remote access, observability, security, packaging, and deployment remain deferred.

## Related Documents

- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Stabilization Checkpoint](stabilization-checkpoint.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Parser To Normalization Integration Recap](parser-to-normalization-integration-recap.md)
- [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)
- [Documentation Map Consistency Checklist](documentation-map-consistency-checklist.md)
- [Review Readiness Checklist](review-readiness-checklist.md)
