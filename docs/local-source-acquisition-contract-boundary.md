# Local Source Acquisition Contract Boundary

This document defines the future local source acquisition contract boundary before any contract, model, or implementation code is added.

It is documentation-only. This task adds no contract/model implementation, file reading behavior, real source data, remote source behavior, credentials/secrets handling, persistence/DB behavior, scheduler/retry/cancel behavior, source adapter behavior, parser behavior, normalization behavior, unit conversion, factor correctness logic, or production readiness.

## Purpose

Local source acquisition is the future boundary for describing source files that are already available locally before they are handed to source adapter execution.

This document outlines the future contract shape and field responsibilities without creating Python or .NET contracts/models. It keeps local acquisition metadata separate from local file reading behavior, source adapter behavior, parser behavior, normalization behavior, persistence, remote acquisition, scheduling/retry, and credential/secrets handling.

## Relationship To Source Acquisition Boundary

[Source Acquisition Boundary](source-acquisition-boundary.md) defines the broader acquisition concepts for local acquisition, remote acquisition, source identity, manifests, checksums, cache, credentials, scheduler/retry/cancel behavior, persistence, and handoff.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) identifies local source acquisition contract/model boundary work as a safe documentation step before implementation. This document fills that step only at the documentation level.

## Future Local Source Acquisition Contract Shape

A future local source acquisition contract may describe:

- Local file path.
- Source identity.
- Source family.
- Source version/date.
- Source file name.
- Source media type or file extension.
- Checksum/hash.
- File size.
- Acquisition timestamp.
- Acquisition mode, such as local/manual.
- Manifest relationship.
- Handoff metadata for source adapter execution.

The eventual contract shape should be deterministic, reviewable, and explicit about which fields are required, optional, derived, or supplied by the caller. Those details should be defined in a future contract/model task with tests.

## Field Responsibilities

Future field responsibilities may include:

- Local file path: identifies where a local file is expected to exist without defining file reading behavior in this document.
- Source identity: distinguishes one source input from another in a stable, reviewable way.
- Source family: connects the local source input to the expected source family vocabulary.
- Source version/date: records a caller-provided or locally derived version/date only when explicitly available.
- Source file name: records the local file name for review and downstream diagnostics.
- Source media type or file extension: describes the expected file shape without proving parser support.
- Checksum/hash: records source content identity when a future task explicitly scopes calculation.
- File size: records local file size metadata when a future task explicitly scopes reading file metadata.
- Acquisition timestamp: records when local acquisition metadata was produced, if explicitly scoped.
- Acquisition mode: distinguishes local/manual acquisition from future remote acquisition.
- Manifest relationship: links local acquisition metadata to a future source manifest without adding manifest implementation.
- Handoff metadata: provides only the fields source adapters need to receive local acquisition output explicitly.

These responsibilities do not prove source adapter correctness for real external sources, parser correctness for real external sources, normalization correctness, unit conversion correctness, factor correctness, legal/compliance interpretation, official carbon accounting correctness, or readiness for production use.

## Boundary Separation

The local source acquisition contract boundary should remain separate from:

- Local file reading behavior: this document does not read files, inspect content, or validate file contents.
- Source adapter behavior: adapters may later consume acquisition metadata, but their runtime behavior is separate.
- Parser behavior: parsers may later consume files through explicit handoff, but parser correctness is separate.
- Normalization behavior: normalization starts after parser/handoff outputs and is separate from acquisition metadata.
- Persistence: DB writes, manifest persistence, and stored acquisition state require separate scope.
- Remote acquisition: remote source locations, downloads, and source URL catalogs require separate scope.
- Scheduler/retry/cancel: orchestration and failure policy require separate scope.
- Credential/secrets handling: local acquisition contracts must not embed real credentials or secrets.

Keeping these boundaries separate prevents a contract documentation task from quietly becoming an implementation or runtime behavior task.

## Handoff To Source Adapters

Future handoff to source adapters should make acquisition metadata explicit.

A future local acquisition output may provide source adapters with:

- Source identity.
- Source family.
- Local file path.
- Source file name.
- Source version/date when available.
- Media type or file extension.
- Checksum/hash metadata when available.
- File size metadata when available.
- Acquisition mode and timestamp when explicitly scoped.
- Manifest reference when a manifest model exists.

Source adapters should not infer hidden acquisition behavior from a local contract. Adapter runtime behavior, parser runtime behavior, parser-to-normalization integration behavior, and normalization runtime behavior remain deferred until separately scoped.

## Review Checklist

Reviewers should confirm:

- The change is documentation-only.
- No Python or .NET contract/model code is added.
- No file reading behavior is added.
- No real source data is added.
- No real source URLs or remote source behavior are added.
- No credentials or secrets handling is added.
- No persistence/DB behavior is added.
- No scheduler, retry, or cancel behavior is added.
- No source adapter, parser, or normalization behavior is changed.
- The document does not imply real source acquisition coverage.
- Public wording avoids source adapter, parser, normalization, unit conversion, factor, compliance, legal, carbon accounting, or production readiness claims.

## Non-Goals

This document does not add, implement, prove, or claim:

- Local source acquisition model implementation.
- Local file reading implementation.
- Real source data.
- Source manifest model implementation.
- Checksum enforcement.
- Source cache implementation.
- DB/persistence behavior.
- Remote download implementation.
- Source URL catalog.
- Credential/secrets handling.
- Scheduler behavior.
- Retry/cancel behavior.
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
- Packaging or deployment.
- Readiness for production use.

## Related Documents

- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Source Ingestion Boundaries](source-ingestion-boundaries.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Production Readiness Gap Analysis](production-readiness-gap-analysis.md)
