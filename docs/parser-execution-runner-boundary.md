# Parser Execution Runner Boundary

This document defines the parser execution runner boundary for future parser adapter execution.

It is a runner boundary only. It does not add source-specific parser adapters, read files, perform HTTP or network calls, execute normalization, write to a database, schedule work, use credentials, or make production parser correctness claims.

## Purpose

`run_parser_execution()` is the narrow boundary that decides whether `ParserAdapter.parse()` may be called. It uses the existing execution planner and returns a `ParserExecutionResult`.

The runner accepts:

- `ParserInputContract`
- `ParserAdapterRegistry` or an iterable of `ParserAdapter`-compatible objects

## Runner Decisions

The runner first creates a `ParserExecutionPlan`.

- `invalid_input` becomes a `failed` `ParserExecutionResult` with validation issues converted into parser execution issues. The runner does not resolve adapters or call `parse()`.
- `no_adapter` becomes an `unsupported` `ParserExecutionResult` with a `PARSER_EXECUTION_NO_ADAPTER` issue. The runner does not call `parse()`.
- `ready` resolves the selected adapter by metadata and calls `parse()` exactly at that boundary.

The runner does not inspect artifact contents. A local path or artifact reference remains metadata passed through the input contract.

Future real source-specific adapters must remain compatible with this runner path. A real adapter may only be called by the runner after input validation and metadata-only adapter resolution produce a `ready` plan.

## Adapter Exceptions

Adapter `parse()` exceptions are converted into a `failed` `ParserExecutionResult` with a `PARSER_EXECUTION_ADAPTER_EXCEPTION` issue. The issue records the exception type and the ready plan status as context.

This keeps no-op or future adapter failures represented as parser execution boundary results without adding retry, scheduling, persistence, or normalization behavior.

## No-Op Adapter

`NoopParserAdapter` may be registered and planned as ready for no-op metadata. If it is run through `run_parser_execution()`, its refusal to parse is represented as a failed parser execution result. It still does not produce real parser output.

## Artificial Success Path

`ArtificialParserAdapter` may be registered to exercise the ready runner path with in-memory metadata only. For matching artificial parser input, `run_parser_execution()` returns the adapter's deterministic `success` `ParserExecutionResult`.

That success result is artificial. Its record count comes from adapter configuration, and its metadata marks that it is not a real source parser result.

## DEFRA/DESNZ Skeleton Path

`DefraDesnzParserAdapter` may produce a `ready` plan for matching DEFRA/DESNZ metadata. When run, it returns its skeleton `unsupported` `ParserExecutionResult` instead of parsing real DEFRA/DESNZ files.

## Non-Goals

This boundary does not add:

- Real source-specific parser execution.
- Real source parser output.
- File content reading.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Source-specific real adapters.

## Related Documents

- [Parser Execution Planning Boundary](parser-execution-planning-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Source-Specific Parser Adapter Boundary](source-specific-parser-adapter-boundary.md)
- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
