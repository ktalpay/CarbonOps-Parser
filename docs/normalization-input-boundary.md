# Normalization Input Boundary

This document defines the normalization input boundary built from parser raw record payloads.

It prepares input shape only. It does not execute normalization, transform values, canonicalize field names, convert units, infer emission categories, read files, perform HTTP or network calls, write to a database, schedule work, use credentials, or claim full normalization support.

## Purpose

`NormalizationInputRecord` represents one raw parser record prepared for a future normalization boundary. It preserves:

- source family
- source id
- record index
- row number when available
- raw fields exactly as supplied by the parser payload
- parser metadata when available
- source context when available

`NormalizationInput` groups records from one parser raw payload. It is input for a future normalization step, not normalized output.

## Raw Payload Source

`create_normalization_input_from_raw_payload()` copies `ParsedRawRecordPayload` into `NormalizationInput`.

`build_normalization_input_from_raw_payload()` returns a structured build result:

- `ready` when the copied input passes shape validation
- `not_ready` when required source identity, records, indexes, or raw field mappings are missing

The copy is intentionally literal. Raw field keys and values are not renamed, trimmed, coerced, classified, unit-converted, or mapped to canonical factor fields.

## Parser Execution Handoff

`build_normalization_input_from_parser_execution_handoff()` accepts a `ParserExecutionNormalizationHandoffResult`.

It creates ready normalization input only when:

- the parser execution handoff is ready
- the handoff contains a raw record payload
- the copied normalization input shape validates

Failed, unsupported, no-records, not-ready, or metadata-only handoffs return not-ready normalization input build results.

## Validation

`validate_normalization_input_record()` and `validate_normalization_input()` check conservative shape only:

- source identity must be present and non-empty
- record index must be a positive integer
- raw fields must be a non-empty mapping
- payload records must include at least one record

Validation does not decide factor correctness, normalize records, or interpret source-owner semantics.

## Minimal DEFRA/DESNZ Mapping

`map_defra_desnz_normalization_input()` can map `NormalizationInput` created from the minimal DEFRA/DESNZ fixture parser path into `NormalizationResult` output wrapped by `DefraDesnzNormalizationMappingResult`.

The mapper copies only the known fixture raw fields `factor_id`, `factor_name`, and `unit`. It preserves source family, source id, record index, and row number. It does not convert units, infer categories, canonicalize fields, read files, call remote services, or claim full DEFRA/DESNZ normalization support.

## Non-Goals

This boundary does not add:

- Normalization execution.
- Value transformation or canonicalization.
- Unit conversion.
- Emission category inference.
- Database persistence fields.
- File reading or source acquisition behavior.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Full source-specific normalization support.

## Related Documents

- [Parsed Raw Record Payload Boundary](parsed-raw-record-payload-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Parser Execution Normalization Handoff Boundary](parser-execution-normalization-handoff-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Normalization Boundary](normalization-boundary.md)
- [Public Safety](public-safety.md)
