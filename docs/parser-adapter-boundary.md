# Parser Adapter Boundary

This document defines the parser adapter interface boundary for future source-specific parser adapters.

It is a contract boundary only. It does not add parser execution, file reading, HTTP or network behavior, normalization execution, database persistence, scheduler behavior, credentials, or source-specific real adapters.

## Purpose

`ParserAdapter` describes the shape future parser adapters should satisfy when they consume `ParserInputContract` metadata. It lets future work distinguish parser adapter compatibility checks from real parser execution.

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

## Execution Planning Boundary

`ParserExecutionPlan` and `plan_parser_execution()` combine `ParserInputContract` validation with metadata-only registry resolution. Planning returns `ready`, `invalid_input`, or `no_adapter` status without calling `parse()`, opening files, making network calls, running normalization, or writing to a database.

## Non-Goals

This boundary does not add:

- Real parser execution.
- Source-specific real adapters.
- Registry-driven parser execution.
- Planning-driven parser execution.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, or background job behavior.
- Credentials or secrets.
- Parser correctness, factor correctness, compliance, legal, or carbon accounting claims.

## Related Documents

- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Public Safety](public-safety.md)
