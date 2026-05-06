# Parsed Raw Record Payload Boundary

This document defines the raw parsed record payload boundary for parser execution results.

It is parser-output shape only. It does not execute normalization, transform or canonicalize values, read files, perform HTTP or network calls, write to a database, schedule work, use credentials, or claim full DEFRA/DESNZ parser support.

## Purpose

`ParsedRawRecord` represents one parser-output raw record before normalization. It preserves the source family, source id, deterministic record index or row number, raw field mapping, optional parser metadata, and optional source context.

`ParsedRawRecordPayload` groups raw records from one parser execution result. The payload is intended for future normalization handoff after parser execution succeeds, but it is not normalized output.

## Raw Fields

`raw_fields` preserves parser-observed values as supplied by the parser boundary. The contract does not rename fields, convert units, coerce value types, trim values, map values to canonical names, or apply source-owner correctness rules.

Future parser implementations may populate raw fields from already-loaded content. File loading remains a separate responsibility.

## Validation

`validate_parsed_raw_record()` and `validate_parsed_raw_record_payload()` check only conservative shape rules:

- `source_family` must be present and non-empty.
- `source_id` must be present and non-empty.
- `record_index` must be a positive integer.
- `raw_fields` must be a non-empty mapping.
- payload child record issues are reported with deterministic `records[N].field` paths.

Validation does not interpret raw values and does not decide whether a record is correct for carbon accounting, legal, compliance, or source-owner purposes.

## Parser Execution Result Integration

`ParserExecutionResult` may carry `raw_record_payload` when a parser boundary has already produced raw records in memory. The field is optional and defaults to `None`, so existing metadata-only parser results remain valid.

The minimal DEFRA/DESNZ content helper attaches a raw payload for the small deterministic CSV-like fixture format when parsing succeeds. That helper still accepts already-loaded `ParserFileContentInput` only; it does not read artifact paths, perform HTTP calls, normalize values, persist records, or implement full DEFRA/DESNZ parsing.

## Normalization Handoff Relationship

`build_parser_execution_normalization_handoff()` can preserve an available raw payload from a successful `ParserExecutionResult`. The handoff status remains about readiness only; it does not execute normalization or transform raw records.

Failed, unsupported, and no-records parser execution results still do not create ready normalization handoffs.

## Normalization Input Relationship

`build_normalization_input_from_raw_payload()` can copy a `ParsedRawRecordPayload` into `NormalizationInput`. The copy preserves source identity, record indexes, row numbers, raw field keys and values, parser metadata, and source context.

`build_normalization_input_from_parser_execution_handoff()` can build normalization input from a ready parser execution handoff only when a raw payload is already present. It returns not-ready results for not-ready handoffs or metadata-only handoffs.

Normalization input remains pre-normalization data. It does not canonicalize fields, transform values, convert units, infer categories, or execute normalization.

## Non-Goals

This boundary does not add:

- Normalization execution.
- Value canonicalization or unit conversion.
- Database persistence fields.
- File reading or source acquisition behavior.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Full source-specific parser support.

## Related Documents

- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Parser Execution Normalization Handoff Boundary](parser-execution-normalization-handoff-boundary.md)
- [Normalization Input Boundary](normalization-input-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Source-Specific Parser Adapter Boundary](source-specific-parser-adapter-boundary.md)
- [Public Safety](public-safety.md)
