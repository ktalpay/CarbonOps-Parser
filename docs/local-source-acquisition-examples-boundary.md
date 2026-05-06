# Local Source Acquisition Examples Boundary

This document defines what future local source acquisition examples may and may not demonstrate.

It is documentation-only. It adds no fixtures, example code, Python code, .NET code, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, DB/persistence behavior, scheduler/retry/cancel behavior, config loading, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future local source acquisition examples should help reviewers understand deterministic local acquisition shapes without implying real source coverage or runtime readiness.

Those examples may show how artificial in-repository inputs could be described for handoff, but they must not demonstrate arbitrary filesystem access, real source discovery, real source correctness, source adapter correctness for real external sources, parser correctness for real external sources, normalization correctness, unit conversion correctness, factor correctness, compliance/legal interpretation, official carbon accounting correctness, or readiness for production use.

## Allowed Example Scope

Future examples may demonstrate:

- Artificial in-repository fixtures only.
- Deterministic example inputs.
- Local-only metadata shapes when explicitly scoped.
- No external network access.
- No real source URLs.
- No credentials.
- No production filesystem assumptions.
- No source correctness claims.
- No parser correctness claims.
- No normalization correctness claims.
- Handoff-shaped metadata for future source adapter examples, without changing source adapter behavior.

Allowed examples should stay small, local, and reviewable. They should make clear that artificial files and deterministic inputs are not evidence of real source acquisition coverage.

## Disallowed Example Scope

Future examples must not demonstrate:

- Reading arbitrary user files.
- Scanning real directories.
- Downloading source documents.
- Storing source metadata in a database.
- Scheduler/retry/cancel behavior.
- Checksum enforcement beyond artificial examples.
- Compliance/legal interpretation.
- Carbon accounting interpretation.
- Credentials/secrets handling.
- Remote access behavior.
- Production filesystem assumptions.
- Parser or normalization correctness for real external sources.

Any item in this section requires a separate future boundary and explicitly scoped implementation task before it can be considered.

## Relationship To Local Source Acquisition Contract Boundary

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) defines future local acquisition contract concepts such as local file path, source identity, source family, source version/date, file name, media type or extension, checksum/hash, file size, acquisition timestamp, acquisition mode, manifest relationship, and source adapter handoff metadata.

Future examples may illustrate those concepts only with artificial, deterministic, in-repository inputs. This document does not add local source acquisition contracts/models or example code.

## Relationship To Source Acquisition Boundary

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

Future local examples should preserve that separation. They should not hide remote acquisition, database writes, scheduler behavior, retry/cancel behavior, credentials/secrets handling, parser behavior, or normalization behavior inside example setup.

## Relationship To Source Adapter Handoff

Source adapter handoff documentation is represented by [Source Adapter Contract](source-adapter-contract.md) and [Source Adapter Execution Flow](source-adapter-execution-flow.md).

Future local source acquisition examples may show handoff-shaped metadata only when the task explicitly scopes that documentation or example boundary. They must not change source adapter runtime behavior, parser behavior, normalization behavior, or public API exports as part of an examples-only task.

## Review Checklist

Future local source acquisition examples should be reviewed for:

- Documentation-only or example-only scope is explicit.
- Inputs are artificial and in-repository.
- Example values are deterministic.
- No real source data is added.
- No real source URLs are added.
- No external network access is shown.
- No credentials or secrets are included.
- No arbitrary user file reads are demonstrated.
- No real directory scanning is demonstrated.
- No production filesystem assumptions are made.
- No DB/persistence behavior is added.
- No scheduler, retry, or cancel behavior is added.
- No checksum enforcement is implied beyond artificial examples.
- No source correctness claim is made.
- No source adapter correctness claim for real external sources is made.
- No parser or normalization correctness claim is made.
- Public safety wording remains clean.

## Non-Goals

This document does not add, implement, prove, or claim:

- Local source acquisition example code.
- Local source acquisition model code.
- Local source acquisition runtime behavior.
- Local file reading behavior.
- Source manifest code.
- Source manifest persistence.
- Real source data.
- Real source URLs.
- Remote download behavior.
- Credentials/secrets handling.
- DB/persistence behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Config loading.
- Deployment behavior.
- Source cache behavior.
- Checksum enforcement beyond artificial examples.
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
- Compliance or legal interpretation.
- Carbon accounting correctness.
- Readiness for production use.

## Related Documents

- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Ingestion Boundaries](source-ingestion-boundaries.md)
- [Production Readiness Gap Analysis](production-readiness-gap-analysis.md)
