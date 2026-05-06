# Source Acquisition Sequencing Checklist

This checklist orders future source acquisition work before any real acquisition behavior is added.

It is documentation-only. This task adds no source acquisition implementation, source contracts/models, real source URLs, remote download behavior, credentials/secrets handling, scheduler/retry/cancel behavior, DB/persistence behavior, source adapter behavior, parser behavior, normalization behavior, unit conversion, or factor correctness logic.

## Purpose

Source acquisition needs a conservative sequence because it can easily cross into remote access, credentials, caching, scheduling, retry, persistence, and parser/runtime behavior.

This checklist helps future tasks move from documentation boundaries toward narrow implementation tasks without bundling unrelated responsibilities. It does not imply real source acquisition coverage, source adapter correctness for real external sources, parser correctness for real external sources, normalization correctness, unit conversion correctness, factor correctness, legal/compliance interpretation, official carbon accounting correctness, or readiness for production use.

## Relationship To Source Acquisition Boundary

[Source Acquisition Boundary](source-acquisition-boundary.md) defines the future concepts and separation points for local acquisition, remote acquisition, source identity, manifests, checksums, cache, credentials, scheduler/retry/cancel behavior, persistence, and handoff to source adapters and parsers.

This checklist turns that boundary into an order of operations. It does not replace the boundary document and does not add contracts, models, tests, or runtime behavior.

## Sequencing Checklist

Future source acquisition work should proceed in this order:

1. Confirm the source acquisition boundary.
2. Define the local source acquisition contract/model boundary.
3. Define the source identity and source version/date model boundary.
4. Define the source manifest boundary.
5. Define the checksum/hash boundary.
6. Define the cache boundary.
7. Define the remote acquisition boundary.
8. Define the credentials/secrets boundary.
9. Define the scheduler/retry/cancel boundary.
10. Define the persistence boundary.
11. Define the handoff to source adapters/parsers.
12. Only then consider narrow implementation tasks.

Each step should stay small and reviewable. Documentation, contracts/models, artificial examples, tests, and runtime implementation should remain separate unless a future task explicitly scopes more than one activity.

## Review Gates

Before moving from documentation into implementation, reviewers should confirm:

- Scope is documented.
- Non-goals are documented.
- No real source URLs are added unless explicitly scoped.
- No credentials/secrets are added.
- No remote download behavior is added unless explicitly scoped.
- No scheduler/retry/cancel behavior is added unless explicitly scoped.
- No DB/persistence behavior is added unless explicitly scoped.
- Tests are planned for any future behavior.
- Public safety wording is clean.
- Deferred items are listed.
- No source adapter, parser, or normalization behavior changes are hidden inside acquisition work.
- No correctness claim is made without explicit scope and tests.

These gates should be repeated for every implementation slice, not just the first source acquisition task.

## What Should Not Be Implemented Yet

The following should not be implemented by this checklist task:

- Source acquisition runtime behavior.
- Source contracts/models.
- Real source URLs.
- Remote download behavior.
- Credentials/secrets handling.
- Scheduler behavior.
- Retry/cancel behavior.
- DB/persistence behavior.
- Source cache behavior.
- Manifest persistence.
- Checksum enforcement.
- Source adapter runtime behavior.
- Parser runtime behavior.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.

Future tasks may implement a narrow item only after the related boundary is documented, tests are planned, and review gates are met.

## Safe Next Task Families

Safe next task families include:

- Local source acquisition contract/model boundary documentation.
- Source identity and source version/date boundary documentation.
- Source manifest boundary documentation.
- Checksum/hash boundary documentation.
- Cache boundary documentation.
- Remote acquisition boundary documentation.
- Credentials/secrets boundary documentation.
- Scheduler/retry/cancel boundary documentation.
- Persistence boundary documentation.
- Source acquisition handoff boundary documentation for source adapters and parsers.

Implementation tasks should come after these boundaries and should remain narrow, deterministic, and reviewable.

## Non-Goals

This checklist does not add, implement, prove, or claim:

- Real source acquisition.
- Remote download implementation.
- Source URL catalog.
- Credential/secrets handling.
- Source cache implementation.
- Manifest persistence.
- DB/persistence behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Checksum enforcement.
- Source adapter runtime behavior.
- Source adapter correctness for real external sources.
- Parser runtime behavior.
- Parser correctness for real external sources.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Normalization correctness.
- Unit conversion.
- Unit conversion correctness.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Observability, logging, or metrics.
- Packaging.
- Deployment.
- Readiness for production use.

## Related Documents

- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Ingestion Boundaries](source-ingestion-boundaries.md)
- [Source Discovery](source-discovery.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Production Readiness Gap Analysis](production-readiness-gap-analysis.md)
- [Production Readiness Sequencing Roadmap](production-readiness-sequencing-roadmap.md)
