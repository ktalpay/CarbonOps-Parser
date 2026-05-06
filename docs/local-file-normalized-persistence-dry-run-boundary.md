# Local File Normalized Persistence Dry-Run Boundary

This document defines the local file to normalized persistence dry-run boundary.

It is a dry-run pipeline only. It may read an explicitly supplied local UTF-8 fixture file and compose existing in-memory helpers. It does not connect to PostgreSQL, write to a database, execute SQL, run migrations, perform HTTP or network calls, schedule work, load configuration, or use credentials.

## Purpose

`run_local_file_normalized_persistence_dry_run()` demonstrates the current local-only vertical slice from an already-acquired DEFRA/DESNZ fixture file to `PersistenceInput` plus PostgreSQL DDL preview metadata.

The helper is intended for boundary testing and troubleshooting. It is not a production ingestion workflow, source acquisition workflow, scheduler, database repository, migration tool, or correctness claim for real DEFRA/DESNZ source files.

## Inputs

The dry-run helper accepts:

- explicit `local_path`
- `source_family`
- `source_id`
- optional `content_type`
- optional `format_hint`
- optional `checksum_sha256`

The path must be local and explicit. The helper does not discover files, download files, inspect manifests, or resolve remote artifact references.

## Checked-In Fixture

The repository includes a minimal local fixture for this boundary:

- `examples/fixtures/defra_desnz_minimal.csv`

The fixture matches the current minimal DEFRA/DESNZ parser and normalization fields: `factor_id`, `factor_name`, and `unit`. It is local dry-run input only, not real source data and not a production DEFRA/DESNZ correctness claim.

## Composed Steps

The dry-run uses only existing safe local and in-memory boundaries:

1. Load local UTF-8 file content into `ParserFileContentInput`.
2. Run the minimal DEFRA/DESNZ fixture content parser.
3. Build the parser execution normalization handoff.
4. Build `NormalizationInput` from raw parser payload.
5. Run the minimal DEFRA/DESNZ fixture normalization mapper.
6. Build `PersistenceInput` from successful normalization output.
7. Attach PostgreSQL DDL preview text as preview metadata only.

Each step preserves its structured result on `LocalFilePersistenceDryRunResult` so failures can be inspected without downstream side effects.

## Status

`LocalFilePersistenceDryRunStatus` includes:

- `success`
- `failed`
- `no_records`
- `unsupported`

Missing local files and malformed fixture content return structured non-success results. Non-success parser or normalization results do not produce ready persistence input.

## DDL Preview Metadata

On success, the dry-run includes `ddl_preview` and `ddl_preview_metadata`.

The DDL preview is review text only. It is not executed, not sent to PostgreSQL, not stored as a migration, and not used to create tables.

## CLI Relationship

`carbonops-parser local-dry-run` and `python -m carbonfactor_parser.cli local-dry-run` provide a command entry path for this helper.

The CLI accepts an explicit local path plus source metadata and prints deterministic text or JSON summary output. It does not scan directories, load configuration files, trigger source acquisition, connect to PostgreSQL, execute SQL, or write records.

## Non-Goals

This boundary does not add:

- PostgreSQL connections.
- Database writes.
- SQL execution.
- Migrations.
- Runtime table creation.
- HTTP or network calls.
- Source acquisition or downloading.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Production ingestion behavior.
- Production DEFRA/DESNZ parsing or normalization correctness claims.

## Related Documents

- [Local Parser File Content Loader Boundary](local-parser-file-content-loader-boundary.md)
- [Local Dry-Run CLI Boundary](local-dry-run-cli-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Parser Execution Normalization Handoff Boundary](parser-execution-normalization-handoff-boundary.md)
- [Normalization Input Boundary](normalization-input-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [Public Safety](public-safety.md)
