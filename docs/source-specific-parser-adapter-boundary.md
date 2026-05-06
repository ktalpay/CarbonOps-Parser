# Source-Specific Parser Adapter Boundary

This document defines implementation boundary rules for future real source-specific parser adapters.

It is a boundary document only. It does not add DEFRA/DESNZ, GHG Protocol, IPCC, or other real parser adapters. It does not parse files, read files, perform HTTP or network calls, execute normalization, write to a database, schedule work, use credentials, or make production parser correctness claims.

## Purpose

Future source-specific parser adapters will translate acquired source artifacts into parser execution results. Before those adapters are implemented, their responsibilities need to stay narrow and explicit so parsing does not absorb acquisition, normalization, persistence, or orchestration concerns.

## Adapter Identity

Each real source-specific parser adapter must declare a stable `source_family` identity that matches the parser input it owns. Examples may include future identifiers for DEFRA/DESNZ, GHG Protocol, or IPCC, but this task does not create those adapters or reserve production behavior.

Adapter identity rules:

- `source_family` must be non-empty and deterministic.
- One registered adapter identity must not silently overlap another adapter identity.
- Source family naming should match existing parser input and acquisition descriptor conventions.
- Adapter metadata must not imply source correctness, compliance approval, or production readiness.

## Capability Metadata

Each adapter should declare metadata-only capability hints:

- `supported_content_types`
- `supported_format_hints`

These values are routing hints for `ParserAdapterRegistry` and `plan_parser_execution()`. They do not prove that artifact contents are valid, current, complete, or suitable for normalization.

## Metadata-Only `can_parse()`

`can_parse(parser_input)` must use only `ParserInputContract` metadata, such as:

- `source_family`
- `source_id`
- `content_type`
- `format_hint`
- acquisition status or run metadata when explicitly needed for compatibility

`can_parse()` must not open artifact paths, inspect file contents, perform HTTP requests, execute parser logic, run normalization, write to a database, access credentials, or schedule work.

## `parse()` Result Boundary

When future real parsing is explicitly scoped, `parse(parser_input)` must return `ParserExecutionResult`.

The result should represent parser execution output only. It may include:

- parser/source identity
- source id
- originating `ParserInputContract`
- parsed record count
- `ParserExecutionIssue` warnings or errors
- parser metadata needed for traceability

The result must not include normalized records, database persistence fields, scheduler state, acquisition retry state, credential material, compliance conclusions, legal conclusions, or carbon accounting correctness claims.

## Issues And Warnings

Source-specific parser adapters should report parser-level issues through `ParserExecutionIssue`.

Use issues for conditions such as unsupported format details, missing expected parser sections, ambiguous parser fields, row-level parser warnings, or parser failures. Acquisition failures remain acquisition status; normalization failures remain normalization issues.

Issue metadata should be deterministic and safe to expose. It should not include secrets, private customer data, or unnecessary raw source content.

## File Reading Boundary

File content reading is deferred from this boundary.

Future file-content input work must explicitly own when and how artifacts are opened, streamed, decoded, size-checked, and handed to source-specific parser logic. Until that task is scoped, parser adapter compatibility checks and boundary documentation must treat artifact references and local paths as metadata only.

`ParserFileContentInput` defines the already-loaded content shape for future parser work. It keeps parseable text or bytes separate from `ParserInputContract` acquisition metadata, and it still does not perform file loading by itself.

## Source Acquisition Separation

Source acquisition owns descriptor discovery, target planning, explicit HTTP acquisition, local artifact references, file metadata, manifests, checksums, and acquisition status.

Parser adapters must not download sources, mutate acquisition manifests, retry acquisition, infer hidden credentials, or reinterpret acquisition status as parsed output. They may receive acquisition metadata through `ParserInputContract` and preserve it for traceability in parser execution results.

## Runner And Planning Relationship

`ParserAdapterRegistry` resolves adapters by metadata-only `can_parse()` checks.

`plan_parser_execution()` validates `ParserInputContract` and resolves candidate adapters without calling `parse()`.

`run_parser_execution()` may call `parse()` only when the plan status is `ready`. It returns `failed` results for invalid input, `unsupported` results when no adapter matches, and the selected adapter's `ParserExecutionResult` for ready plans.

Future source-specific adapters should remain compatible with this planner and runner path. They must not rely on side effects from planning or registry resolution.

## DEFRA/DESNZ Skeleton Status

`DefraDesnzParserAdapter` is the current DEFRA/DESNZ source-specific parser adapter skeleton. It declares deterministic `defra_desnz` identity and DEFRA/DESNZ format metadata for registry, planning, and runner wiring tests.

Its `can_parse()` behavior is metadata-only. Its `parse()` method returns an `unsupported` `ParserExecutionResult` with a `DEFRA_DESNZ_PARSER_NOT_IMPLEMENTED` issue. It does not read artifact paths, parse real DEFRA/DESNZ content, execute normalization, write to a database, perform network calls, or claim real DEFRA/DESNZ support.

## Minimal Implementation Checklist

Before a real source-specific parser adapter is added, reviewers should confirm:

- The task explicitly names the source adapter being implemented.
- `source_family` is stable and matches the intended parser input.
- `supported_content_types` and `supported_format_hints` are deterministic.
- `can_parse()` is metadata-only.
- `parse()` returns `ParserExecutionResult`.
- Parser warnings and errors use `ParserExecutionIssue`.
- File content ownership is explicitly scoped for that task.
- No acquisition, normalization, database, scheduler, credential, or network behavior is added accidentally.
- Tests prove the adapter does not handle unrelated source families.
- Documentation avoids production, compliance, legal, and carbon accounting correctness claims.

## Non-Goals

This boundary does not add:

- DEFRA/DESNZ parser implementation.
- GHG Protocol parser implementation.
- IPCC parser implementation.
- Real source-specific parser execution.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Production parser correctness claims.

## Related Documents

- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Parser Execution Runner Boundary](parser-execution-runner-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Public Safety](public-safety.md)
