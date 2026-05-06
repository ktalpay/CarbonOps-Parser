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

## Non-Goals

This boundary does not add:

- Real parser execution.
- Source-specific real adapters.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, or background job behavior.
- Credentials or secrets.
- Parser correctness, factor correctness, compliance, legal, or carbon accounting claims.

## Related Documents

- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Public Safety](public-safety.md)
