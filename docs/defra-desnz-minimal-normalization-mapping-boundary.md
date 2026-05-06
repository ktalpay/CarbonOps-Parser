# DEFRA/DESNZ Minimal Normalization Mapping Boundary

This document defines the minimal DEFRA/DESNZ fixture normalization mapping boundary.

It is a fixture mapping path only. It does not read files, perform HTTP or network calls, write to a database, schedule work, use credentials, infer emission categories, convert units, or claim full DEFRA/DESNZ normalization support.

## Purpose

`map_defra_desnz_normalization_input()` accepts `NormalizationInput` created from parser raw payloads and returns a structured `DefraDesnzNormalizationMappingResult`.

The mapper supports only the small in-memory fixture shape produced by the minimal DEFRA/DESNZ content parser:

- `factor_id`
- `factor_name`
- `unit`

Those values are copied into existing `NormalizedRecord` output fields. The mapper also preserves source family, source id, record index, and row number.

## Status Values

`DefraDesnzNormalizationMappingStatus` reports:

- `success` when all input records contain the required fixture fields
- `failed` when required fixture fields are missing or the source family is not `defra_desnz`
- `no_records` when input contains no records

Structured issues are returned through `NormalizationResult.issues`.

## What Is Copied

The mapper copies only known fixture raw fields. It does not copy unrelated raw fields, does not canonicalize field names, and does not trim or coerce values.

`unit` is copied directly from raw input. No unit conversion is performed.

No emission category is inferred. Future category mapping requires a separate explicitly scoped task.

## In-Memory Pipeline Relationship

A fully in-memory fixture path can be assembled from:

1. `ParserFileContentInput`
2. `parse_defra_desnz_file_content()`
3. `build_parser_execution_normalization_handoff()`
4. `build_normalization_input_from_parser_execution_handoff()`
5. `map_defra_desnz_normalization_input()`

This path remains local and deterministic. It does not read artifact references or claim full source-specific correctness.

## Non-Goals

This boundary does not add:

- Full DEFRA/DESNZ normalization.
- Source-owner correctness checks.
- Unit conversion.
- Emission category inference.
- File reading.
- HTTP or network behavior.
- Database persistence.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.

## Related Documents

- [Normalization Input Boundary](normalization-input-boundary.md)
- [Parsed Raw Record Payload Boundary](parsed-raw-record-payload-boundary.md)
- [Parser Execution Normalization Handoff Boundary](parser-execution-normalization-handoff-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Public Safety](public-safety.md)
