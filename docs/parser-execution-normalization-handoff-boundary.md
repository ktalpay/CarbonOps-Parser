# Parser Execution Normalization Handoff Boundary

This document defines the boundary for handing successful parser execution results to future normalization.

It is a handoff contract only. It does not execute normalization, transform records, read files, perform HTTP or network calls, write to a database, schedule work, use credentials, or claim production parser or normalization correctness.

## Purpose

`ParserExecutionResult` describes parser execution outcome metadata. It currently carries parser/source identity, parsed record count, parser issues, optional parser metadata, and optional raw parsed record payload.

`build_parser_execution_normalization_handoff()` converts only successful parser execution results into a ready normalization handoff. Non-success parser statuses produce a structured not-ready result.

## Handoff Status

`ParserExecutionNormalizationHandoffResult` reports:

- `ready` when the parser execution result status is `success`.
- `not_ready` when the parser execution result status is `failed`, `unsupported`, or `no_records`.

Ready handoffs preserve:

- source family
- source id
- parser status
- parsed record count
- parser metadata
- `parsed_records_payload_status` set to `available` when a raw parser payload is present, otherwise `deferred`
- raw parser payload when it was already present on the successful parser execution result

Raw parser payload preservation is intentionally passive. The handoff does not convert raw parser records into normalized records, and a deferred payload marker still records cases where parser execution produced only metadata.

## Non-Ready Results

Failed, unsupported, and no-records parser execution results do not create ready normalization handoffs. They return a structured issue explaining that the parser execution result must be successful before normalization handoff is ready.

## Non-Goals

This boundary does not add:

- Normalization execution.
- Record normalization or transformation.
- Raw record payload transformation.
- File reading.
- HTTP or network calls.
- Database persistence.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Production parser or normalization correctness claims.

## Related Documents

- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Parsed Raw Record Payload Boundary](parsed-raw-record-payload-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Normalization Boundary](normalization-boundary.md)
- [Public Safety](public-safety.md)
