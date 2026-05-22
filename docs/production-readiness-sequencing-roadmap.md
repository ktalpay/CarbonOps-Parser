# Production Readiness Sequencing Roadmap

This roadmap orders future work that would be needed before CarbonOps-Parser
could be reviewed for project-level production use.

PROD-002 supersedes any Python-only interpretation of project-level production
readiness. The Python runtime has a production operator path; the .NET runtime
is not production-ready yet; project-level production-ready is blocked until
both runtimes pass the production parity contract.

It is documentation-only. It does not implement production readiness, certify production readiness, or add runtime behavior.

## Purpose

The repository currently has public documentation, contracts, artificial
examples, skeletons, governance smoke tests, and a Python runtime production
operator path. Those artifacts help future contributors work in small,
reviewable increments, but they do not make the repository project-level
production-ready.

This document proposes a safe order for future production readiness work. It does not prove parser, normalization, unit conversion, factor, compliance, legal, or carbon accounting correctness. Real behavior must be added only in future narrow tasks with tests and review gates.

## Relationship To Production Readiness Gap Analysis

[Production Readiness Gap Analysis](production-readiness-gap-analysis.md) identifies the missing areas across Python, .NET, shared runtime behavior, operations, testing, packaging, deployment, security, and cross-language validation.

This roadmap does not replace that gap analysis. It turns the deferred areas into a conservative sequence so future tasks can avoid bundling unrelated behavior.

## Sequencing Principles

Future work should follow these principles:

- Document boundaries before implementation.
- Keep source acquisition, parser behavior, normalization behavior, persistence, scheduling, and release behavior in separate task families.
- Add implementation behavior only in explicitly scoped implementation tasks.
- Add or update tests with the behavior they protect.
- Avoid correctness claims unless the scope and tests explicitly support the claim.
- Keep public wording clean of production, compliance, legal, carbon accounting, factor, or source coverage overclaims.
- Keep tasks small enough for focused review.

## Proposed Phases

### Phase 0: Boundary And Scope Confirmation

Confirm the production readiness boundary, non-goals, public wording constraints, and review checklist before real behavior is added.

Expected output should remain documentation-first:

- Scope boundaries for production readiness work.
- Explicit non-goals.
- Review gates for future implementation tasks.
- Deferred area lists kept in sync with related docs.

### Phase 1: Python Runtime Hardening Foundations

Define the Python runtime hardening plan before changing behavior.

Future tasks may scope:

- Python runtime boundary docs.
- Error and validation boundary docs.
- Public API stability notes.
- Test strategy for Python behavior that already has public contracts or artificial examples.

This historical phase did not by itself make the Python path ready for
production use. Later Python operator work established the current Python
runtime production path.

### Phase 2: Source Acquisition And Local/Remote Source Boundaries

Define how source acquisition should be reviewed before real acquisition behavior exists.

Future tasks may scope:

- Local source boundary docs.
- Remote source boundary docs.
- Source version/hash boundary docs.
- Archive and provenance boundary docs.
- Explicit rules for avoiding hidden real data or credentials.

This phase does not add real source acquisition, real URLs, downloads, or remote access.

### Phase 3: Parser Correctness And Validation Strategy

Define parser correctness boundaries before real parser behavior is hardened.

Future tasks may scope:

- Parser validation strategy.
- Source-specific format drift handling.
- Unsupported row and warning boundaries.
- Reviewer-visible assumptions.
- Test fixture boundaries.

This phase does not prove parser correctness or change parser behavior.

### Phase 4: Normalization, Unit Conversion, And Factor Correctness Boundaries

Define normalization, unit conversion, and factor correctness boundaries before implementation.

Future tasks may scope:

- Normalization runtime boundaries.
- Unit conversion boundary docs.
- Factor correctness boundary docs.
- Parser-to-normalization integration boundaries.
- Test strategy for deterministic conversion and factor validation behavior once explicitly scoped.

This phase does not implement unit conversion, factor correctness logic, or carbon accounting correctness.

### Phase 5: Persistence/Configuration/Scheduler/Retry Boundaries

Define runtime infrastructure boundaries before adding operational behavior.

Future tasks may scope:

- Config loading boundaries.
- DB/persistence boundaries.
- Scheduler boundaries.
- Retry/cancel boundaries.
- Idempotency and recovery boundaries.

This phase does not add config loading, DB behavior, scheduler behavior, retry/cancel logic, or persistence behavior.

### Phase 6: Observability/Security/Operational Hardening

Define supportability and operational safety expectations before implementation.

Future tasks may scope:

- Observability/logging/metrics boundaries.
- Security and secrets handling boundaries.
- Failure diagnostics.
- Operational run summaries.
- Local development safety rules.

This phase does not add observability, logging, metrics, secrets handling, or operational runtime behavior.

### Phase 7: .NET Parity Design

Design .NET parity against documented contracts before implementation.

Future tasks may scope:

- .NET project shape documentation.
- Contract parity mapping.
- Cross-language terminology alignment.
- Differences that are intentional for .NET runtime conventions.

This phase does not add .NET implementation parity.

### Phase 8: .NET Implementation Parity

Add .NET behavior only after parity design is reviewed.

Future tasks may scope:

- .NET contracts and models.
- .NET artificial examples.
- .NET runtime behavior slices.
- .NET tests tied to explicit behavior.

This phase should follow documented contracts rather than inventing parallel behavior.

### Phase 9: Cross-Language Contract Validation

Validate consistency after Python contracts stabilize and .NET parity surfaces exist.

Future tasks may scope:

- Shared contract fixtures.
- Cross-language schema checks.
- Documentation explaining allowed language-specific differences.
- Focused tests for agreed contract behavior.

This phase does not assume cross-language consistency before both paths have reviewed surfaces.

### Phase 10: Packaging/Deployment/Release Review

Review packaging, deployment, and release boundaries after runtime behavior, tests, and operational concerns are explicitly scoped.

Future tasks may scope:

- Packaging boundaries.
- Deployment boundaries.
- Versioning and release notes.
- Compatibility expectations.
- Final production readiness review criteria.

This phase does not publish packages, deploy services, or certify readiness for production use.

## Phase Transition Gates

Before moving from one phase to the next, reviewers should confirm:

- Scope is documented.
- Non-goals are documented.
- Tests are updated for any behavior added, or explicitly unchanged for documentation-only tasks.
- Public safety wording is clean.
- No hidden real data or credentials are added.
- No correctness claim is made without explicit tests and scope.
- Implementation behavior is added only in explicitly scoped implementation tasks.
- Deferred production-grade areas remain deferred unless the task explicitly scopes them.

## Python-First Rationale

Python should generally be hardened first because the current repository already has more public Python artifacts, including contracts, artificial examples, parser handoff shapes, normalization shapes, and public API smoke tests.

This is a sequencing rationale only. It is not a claim that the Python path is ready for production use.

Hardening Python first gives future .NET work a reviewed contract surface to follow. It also reduces the risk that .NET parity work invents parallel behavior before shared expectations are stable.

## .NET Parity Rationale

.NET parity should follow documented contracts rather than inventing a separate workflow. The .NET implementation can still use .NET-oriented structure, naming, and runtime conventions, but shared behavior should trace back to reviewed concepts.

Cross-language consistency should be validated after Python contracts stabilize and .NET parity surfaces exist. Contract validation before both surfaces exist would be premature.

## Non-Goals

This roadmap does not add, implement, prove, or certify:

- Real source acquisition.
- Source adapter runtime behavior.
- Parser runtime behavior.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Real source data handling.
- File I/O beyond current local/artificial examples.
- Config loading.
- DB/persistence behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Downloading or remote access.
- Observability, logging, or metrics.
- Security/secrets handling.
- Packaging or deployment.
- Python production hardening.
- .NET parity implementation.
- Cross-language contract validation.

## Related Documents

- [Production Readiness Gap Analysis](production-readiness-gap-analysis.md)
- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Stabilization Checkpoint](stabilization-checkpoint.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Documentation Map Consistency Checklist](documentation-map-consistency-checklist.md)
- [Review Readiness Checklist](review-readiness-checklist.md)
