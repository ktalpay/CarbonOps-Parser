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

Future real source-specific adapters must use this result boundary for parser output only. Parser execution results should not carry normalized records, database persistence fields, acquisition retry state, scheduler state, or production correctness claims.

## Runner Results

`run_parser_execution()` returns `ParserExecutionResult` for each planning outcome:

- `invalid_input` plans become `failed` results with validation issues converted into parser execution issues.
- `no_adapter` plans become `unsupported` results with a `PARSER_EXECUTION_NO_ADAPTER` issue.
- `ready` plans call the selected adapter's `parse()` boundary and return that adapter's `ParserExecutionResult`.

If an adapter raises while parsing, the runner converts the exception into a `failed` result with a `PARSER_EXECUTION_ADAPTER_EXCEPTION` issue. This preserves a structured boundary result without adding retry, persistence, or normalization behavior.

## Minimal Content Parser Results

Minimal already-loaded content helpers, such as `parse_defra_desnz_file_content()`, also return `ParserExecutionResult`. They may report `success` with a parsed record count, `no_records` for empty in-memory content, or `failed` for invalid fixture shape. They must not include normalized records or persistence output.

## Normalization Handoff

`build_parser_execution_normalization_handoff()` creates a ready normalization handoff only from `success` parser execution results. Failed, unsupported, and no-records parser execution results become structured not-ready handoff results.

The handoff preserves parser/source identity and parsed record count. It does not invent parsed record payloads; `parsed_records_payload_status` remains `deferred` until a future parser payload mapping task is explicitly scoped.

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
- [Source-Specific Parser Adapter Boundary](source-specific-parser-adapter-boundary.md)
- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Parser Execution Runner Boundary](parser-execution-runner-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Parser Execution Normalization Handoff Boundary](parser-execution-normalization-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
