# Parser Execution Result Boundary

This document defines parser execution result contracts for future parser adapters.

It is result-shape only. It does not implement parser execution, read files, perform HTTP or network calls, execute normalization, write to a database, schedule work, use credentials, or add source-specific real adapters.

## Purpose

`ParserExecutionResult` represents the outcome a future parser adapter may return after parser execution is explicitly implemented. It is distinct from normalization output and persistence output.

## Status Values

Parser execution result statuses are:

- `success`
- `failed`
- `unsupported`
- `no_records`

The result carries parser/source identity, the originating `ParserInputContract`, parsed record count, structured issues, and optional parser metadata.

`ParserExecutionIssue` carries deterministic issue metadata: code, message, severity, optional location, and optional context.

## Protocol Alignment

`ParserAdapter.parse()` is typed to return `ParserExecutionResult`. This aligns future parser adapter implementations with the execution result boundary while still leaving real parsing deferred.

## Non-Goals

This boundary does not add:

- Real parser execution.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, or background job behavior.
- Credentials or secrets.
- Source-specific real adapters.
- Production parser correctness claims.

## Related Documents

- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
