# Parser Execution Planning Boundary

This document defines the parser execution planning boundary for future parser adapter execution.

It is planning-only. It does not call `parse()`, read files, perform HTTP or network calls, execute normalization, write to a database, schedule work, use credentials, or add source-specific real adapters.

## Purpose

`ParserExecutionPlan` records the decision that can be made before parser execution exists. It combines parser input validation with metadata-only parser adapter registry resolution.

## Planner Inputs

`plan_parser_execution()` accepts:

- `ParserInputContract`
- `ParserAdapterRegistry` or an iterable of `ParserAdapter`-compatible objects

The planner validates the input contract first. If input validation fails, it returns an `invalid_input` plan and does not resolve adapters.

## Plan Status

The planning status values are:

- `ready`: input is valid and a compatible adapter was selected by metadata.
- `invalid_input`: input contract validation failed.
- `no_adapter`: input is valid, but no adapter matched by metadata.

The plan records the input contract, validation result, selected adapter source family when ready, and issue codes or reasons when planning cannot become ready.

`NoopParserAdapter` can be used in planning tests to produce a `ready` plan for deterministic no-op metadata. It still does not make planning equivalent to parser execution, and its `parse()` method does not produce parser output.

`ParserExecutionResult` is the separate future result boundary for parser execution outcomes. Planning does not create execution results because it does not call `parse()`.

## Non-Goals

This boundary does not add:

- Real parser execution.
- Calls to `parse()`.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, or background job behavior.
- Credentials or secrets.
- Source-specific real adapters.

## Related Documents

- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
