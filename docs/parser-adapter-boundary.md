# Parser Adapter Boundary

This document defines the parser adapter interface boundary for future source-specific parser adapters.

It is a contract boundary only. It does not add parser execution, file reading, HTTP or network behavior, normalization execution, database persistence, scheduler behavior, credentials, or source-specific real adapters.

## Purpose

`ParserAdapter` describes the shape future parser adapters should satisfy when they consume `ParserInputContract` metadata. It lets future work distinguish parser adapter compatibility checks from real parser execution.

Future real source-specific adapters must also follow the source-specific parser adapter boundary. That boundary keeps adapter identity, capability metadata, result shape, file-content ownership, source acquisition separation, normalization separation, and persistence separation explicit before any DEFRA/DESNZ, GHG Protocol, IPCC, or other real adapter is added.

## Interface Shape

The public parser adapter protocol exposes:

- `source_family`
- `supported_content_types`
- `supported_format_hints`
- `can_parse(parser_input)`
- `parse(parser_input)`

`can_parse()` is intended for metadata-only compatibility checks against `ParserInputContract`. It should rely on fields such as source family, content type, and format hint. It should not open artifact paths, call remote services, execute parser logic, run normalization, or write to a database.

`parse()` is a future parser execution boundary. This task defines only the protocol method; it does not implement real parsing.

## Registry Boundary

`ParserAdapterRegistry` provides a deterministic registry boundary for future parser adapters. It accepts `ParserAdapter`-compatible objects, preserves registration order for listing and resolution, and rejects duplicate `source_family` registrations so adapter identity stays explicit.

Registry resolution uses `can_parse(parser_input)` only. It must not call `parse()`, open artifact paths, call remote services, run normalization, or write to a database.

## No-Op Adapter

`NoopParserAdapter` is a metadata-only adapter implementation for registry and planning tests. It advertises `source_family` as `noop`, supports the deterministic no-op content type and format hint, and uses `ParserInputContract` metadata in `can_parse()`.

`NoopParserAdapter.parse()` does not parse files or produce parser output. It raises `NotImplementedError` so no-op planning cannot be mistaken for real parser execution.

## Artificial Adapter

`ArtificialParserAdapter` is an explicitly artificial in-memory adapter for demo and boundary tests. It advertises `source_family` as `artificial`, supports deterministic artificial content type and format hint metadata, and uses only `ParserInputContract` metadata in `can_parse()`.

`ArtificialParserAdapter.parse()` returns a deterministic `ParserExecutionResult` for matching artificial input. Its parsed record count comes from adapter configuration, not artifact file contents. Result metadata marks the adapter kind as artificial and records that it is not a real source parser.

This adapter must not be used to represent DEFRA/DESNZ, GHG Protocol, IPCC, or any other real source-specific parsing behavior.

## DEFRA/DESNZ Adapter Skeleton

`DefraDesnzParserAdapter` is a source-specific parser adapter skeleton. It advertises `source_family` as `defra_desnz` and supports deterministic DEFRA/DESNZ content type and format hint metadata for registry, planning, and runner coverage.

`DefraDesnzParserAdapter.parse()` returns an `unsupported` `ParserExecutionResult` with a not-implemented issue. It does not read files or parse real DEFRA/DESNZ content.

## Execution Planning Boundary

`ParserExecutionPlan` and `plan_parser_execution()` combine `ParserInputContract` validation with metadata-only registry resolution. Planning returns `ready`, `invalid_input`, or `no_adapter` status without calling `parse()`, opening files, making network calls, running normalization, or writing to a database.

## Execution Result Boundary

`ParserExecutionResult` defines future parser execution outcomes such as `success`, `failed`, `unsupported`, and `no_records`. It is parser-output metadata only and does not include normalized records or persistence fields. `ParserAdapter.parse()` is typed to return `ParserExecutionResult`, but real parser execution remains deferred.

## Non-Goals

This boundary does not add:

- Real parser execution.
- Source-specific real adapters.
- No-op parser output.
- Real source parser output.
- Normalized parser output.
- Real registry-driven parser execution.
- Real planning-driven parser execution.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, or background job behavior.
- Credentials or secrets.
- Parser correctness, factor correctness, compliance, legal, or carbon accounting claims.

## Related Documents

- [Source-Specific Parser Adapter Boundary](source-specific-parser-adapter-boundary.md)
- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Public Safety](public-safety.md)
