# Source Acquisition Boundary

This document defines future source acquisition responsibilities and boundaries before any real acquisition behavior is added.

It is documentation-only. This task adds no source acquisition implementation, real source URLs, remote download behavior, credentials or secrets handling, scheduler/retry/cancel behavior, DB/persistence behavior, source adapter behavior, parser behavior, normalization behavior, unit conversion, or factor correctness logic.

## Purpose

Source acquisition is the future boundary responsible for obtaining or locating source documents before they are handed to source adapters and parsers.

The current repository has local and artificial examples that help demonstrate contract shape and deterministic workflows. Existing local/artificial examples do not imply production source acquisition coverage, real source coverage, parser correctness for real external sources, normalization correctness, factor correctness, legal/compliance interpretation, official carbon accounting correctness, or readiness for production use.

This document records the concepts that future tasks should define before implementation begins.

## Current Baseline

The current public baseline includes:

- Source adapter contracts and artificial/local examples.
- Source document metadata and hashing helpers.
- Parser contracts and artificial parser examples.
- Parser-to-normalization handoff models.
- Artificial normalization examples and recaps.
- Documentation maps, checkpoints, and governance smoke tests.

The current baseline does not include real source acquisition, remote source downloads, source URL catalogs, credentials handling, cache behavior, scheduler behavior, retry/cancel behavior, manifest persistence, or DB/persistence behavior.

## Future Source Acquisition Responsibilities

Future source acquisition tasks may define responsibilities such as:

- Identifying a source family and source identity.
- Locating a source document from a local path or remote location.
- Recording source version/date information when explicitly available.
- Producing a source manifest for downstream review.
- Computing or recording checksum/hash values.
- Applying cache boundaries without hiding source provenance.
- Separating credential and secrets handling from public examples.
- Separating scheduler, retry, and cancel behavior from acquisition semantics.
- Handing acquired source document metadata to source adapters or parsers.

Each responsibility should be introduced through a narrow future task with tests and review gates when behavior is added.

## Boundary Separation

Source acquisition should remain separate from:

- Source adapter execution: adapter behavior should consume documented acquisition output rather than own unrelated download, retry, scheduler, or credential logic.
- Parser execution: parsers should receive explicit source inputs and should not be responsible for locating or downloading sources.
- Normalization execution: normalization should consume parser/handoff outputs and should not acquire source documents.
- Persistence: acquisition may produce metadata for future persistence, but DB writes require separately scoped persistence work.
- Scheduling/retry: acquisition may be invoked by future orchestration, but scheduler, retry, and cancel behavior require separate boundaries.
- Credentials/secrets handling: acquisition may need future secret-aware configuration, but public docs and examples must not include real credentials.

This separation keeps source discovery, runtime acquisition, parsing, normalization, persistence, and operations reviewable as separate changes.

## Local Source Boundary

Local source acquisition refers to future behavior that locates source documents already present on the local filesystem.

Future local source tasks should define:

- Allowed local path inputs.
- Expected file metadata.
- Source identity requirements.
- Source version/date handling when available locally.
- Checksum/hash calculation boundaries.
- Manifest fields passed downstream.
- Validation errors for missing, unsupported, or ambiguous local inputs.

Local source acquisition should not imply remote source coverage or parser correctness. File I/O beyond current local/artificial examples remains deferred until explicitly scoped.

## Remote Source Boundary

Remote source acquisition refers to future behavior that obtains source documents from remote locations.

Future remote source tasks should define:

- How remote locations are represented without hard-coding real source URLs into public examples unless explicitly scoped.
- How version/date metadata is discovered or recorded.
- How downloaded content is checked, cached, and handed downstream.
- How download errors are reported without owning scheduler or retry policy.
- How credentials/secrets boundaries are enforced.

This document adds no remote download implementation, remote access behavior, source URL catalog, credentials, or real source data.

## Manifest And Source Identity

A future source manifest should describe acquisition output in a reviewable, deterministic shape.

Future manifest concepts may include:

- Source family.
- Source name.
- Source identity.
- Source version/date.
- Acquisition mode, such as local or remote.
- Local file reference or future remote reference metadata.
- Checksum/hash metadata.
- Content type or file extension.
- Acquisition timestamp or run context when explicitly scoped.
- Warnings or validation issues.

Manifest design should support handoff to source adapters and parsers without making persistence, scheduler, retry, cache, or credential behavior implicit.

## Cache/Checksum Considerations

Cache and checksum behavior should be documented before implementation.

Future tasks may define:

- Whether a source cache exists.
- What metadata identifies cache entries.
- Whether checksum/hash values are advisory or enforced.
- How mismatches are reported.
- How cache invalidation is requested.
- What data is safe to store in public examples.

This document does not add source cache implementation, checksum enforcement, manifest persistence, or DB behavior.

## Credentials And Security Boundary

Credentials and secrets handling must remain separate from public source examples and source manifests.

Future credential/security tasks should define:

- Where sensitive values are configured.
- Which metadata may be logged or included in manifests.
- How missing credentials are reported.
- How public examples avoid real credentials.
- How local development placeholders are kept non-sensitive.

This document adds no credentials, secrets handling, or security runtime behavior.

## Scheduler/Retry/Cancel Boundary

Source acquisition should not implicitly own scheduler, retry, or cancel behavior.

Future scheduler/retry/cancel tasks should define:

- Which component invokes acquisition.
- How retry policy is selected.
- How cancellation is requested and observed.
- How partial acquisition attempts are reported.
- How repeated runs avoid hiding source identity or checksum changes.

This document adds no scheduler behavior, retry/cancel logic, background job behavior, or orchestration behavior.

## Handoff To Source Adapters And Parsers

Future acquisition output should be handed to source adapters and parsers through explicit contracts.

The handoff should preserve:

- Source identity.
- Source version/date metadata when available.
- Manifest information.
- Checksum/hash metadata.
- Local file references or future remote acquisition metadata.
- Warnings or validation issues relevant to downstream processing.

Source adapters and parsers should not infer hidden acquisition behavior. Parser runtime behavior, parser-to-normalization integration behavior, and normalization runtime behavior remain separate concerns.

## Non-Goals

This document does not add, implement, prove, or claim:

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
- Parser runtime behavior.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Observability, logging, or metrics.
- Packaging or deployment.
- Parser correctness for real external sources.
- Normalization correctness.
- Readiness for production use.

## Review Checklist

Reviewers should confirm:

- The change is documentation-only.
- No real source URLs are added.
- No real source data is added.
- No remote download behavior is added.
- No credentials or secrets handling is added.
- No scheduler, retry, or cancel behavior is added.
- No DB/persistence behavior is added.
- No source adapter, parser, or normalization behavior is changed.
- Existing local/artificial examples are not presented as production source acquisition coverage.
- Public wording avoids parser, normalization, unit conversion, factor, compliance, legal, carbon accounting, or production readiness claims.

## Related Documents

- [Source Ingestion Boundaries](source-ingestion-boundaries.md)
- [Source Discovery](source-discovery.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Production Readiness Gap Analysis](production-readiness-gap-analysis.md)
- [Production Readiness Sequencing Roadmap](production-readiness-sequencing-roadmap.md)
