# Local Dry-Run CLI Boundary

This document defines the local dry-run CLI boundary.

It is a command entry path only. It accepts an explicit local DEFRA/DESNZ fixture file path and calls `run_local_file_normalized_persistence_dry_run()`. It does not connect to PostgreSQL, write to a database, execute SQL, run migrations, perform HTTP or network calls, scan directories, load configuration files, trigger source acquisition, schedule work, or use credentials.

## Command

Install the local console script from a working copy with:

```bash
python -m pip install -e .
```

Module invocation:

```bash
python -m carbonfactor_parser.cli local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
```

Console script:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
```

`--content-type` or `--format-hint` must be supplied.

## Output

Text output includes deterministic summary fields:

- dry-run status
- parsed record count
- normalization record count
- persistence input record count
- whether DDL preview text is present
- issue count
- stage, severity, code, and message for issues

JSON output is available with:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --format-hint csv \
  --json
```

JSON output includes intermediate status fields and DDL preview text as metadata. The DDL preview is not executed.

## PostgreSQL Preview Option

The command can include PostgreSQL insert preview data with:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --format-hint csv \
  --include-postgresql-preview
```

Without `--include-postgresql-preview`, local dry-run output remains the
existing summary shape. With the flag, text output includes a deterministic
PostgreSQL preview section and JSON output includes
`postgresql_persistence_preview`.

The preview section is built by `build_postgresql_persistence_preview()` from
ready `PersistenceInput`. It can include:

- preview status
- target table
- ordered columns
- ordered parameter rows
- record count
- SQL text with placeholders
- idempotency key fields
- conflict target fields

If the dry-run has no ready `PersistenceInput`, the PostgreSQL preview section
reports a non-ready status and omits SQL preview data. It must not imply
persistence success.

Expected preview text lines for the checked-in fixture include:

```text
postgresql_preview_included=True
postgresql_preview_status=ready
postgresql_preview_only=True
postgresql_preview_sql_execution=False
postgresql_preview_database_connection=False
postgresql_preview_target_table=normalized_records
postgresql_preview_record_count=2
postgresql_preview_issue_count=0
```

JSON preview output is available with:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --format-hint csv \
  --json \
  --include-postgresql-preview
```

Trimmed JSON preview section:

```json
{
  "postgresql_persistence_preview": {
    "preview_only": true,
    "sql_execution": false,
    "database_connection": false,
    "status": "ready",
    "target_table": "normalized_records",
    "record_count": 2,
    "ordered_columns": [
      "source_family",
      "source_id",
      "record_id",
      "record_index",
      "row_number",
      "normalized_fields",
      "source_reference",
      "source_artifact_reference",
      "source_checksum_sha256",
      "parser_metadata",
      "normalization_metadata",
      "created_at",
      "updated_at"
    ],
    "issues": []
  }
}
```

No PostgreSQL server, database configuration, or credentials are required for
either preview command.

## Checked-In Fixture

The repository includes a tiny local fixture at:

- `examples/fixtures/defra_desnz_minimal.csv`

It contains only the currently supported minimal fields:

- `factor_id`
- `factor_name`
- `unit`

Expected text summary for the fixture:

```text
status=success
parsed_record_count=2
normalization_record_count=2
persistence_input_record_count=2
ddl_preview_present=True
issue_count=0
```

Trimmed JSON output:

```json
{
  "status": "success",
  "parsed_record_count": 2,
  "normalization_record_count": 2,
  "persistence_input_record_count": 2,
  "ddl_preview_present": true,
  "source_family": "defra_desnz",
  "source_id": "defra-desnz-minimal-fixture",
  "issues": []
}
```

The fixture is local dry-run input only. It is not source acquisition, does not use real source data, and does not make production DEFRA/DESNZ correctness claims.

## Exit Codes

The command returns:

- `0` for `success`
- non-zero for `failed`, `unsupported`, and `no_records`
- `2` for argument errors from the CLI parser

## Troubleshooting Relationship

Expected non-success outcomes are documented in [Local Dry-Run Troubleshooting](local-dry-run-troubleshooting.md). That guide covers missing paths, nonexistent files, directories, invalid UTF-8 or binary-like content, invalid parser headers, missing required normalization fields, no-record outcomes, and unsupported loader outcomes.

## Safety Boundaries

The command is explicit-path only. It does not auto-discover files, scan directories, load configuration files, or call source acquisition.

The command composes only existing local/in-memory boundaries:

- local UTF-8 file loader
- minimal DEFRA/DESNZ fixture parser
- parser execution normalization handoff
- normalization input builder
- minimal DEFRA/DESNZ fixture normalization mapper
- persistence input builder
- PostgreSQL DDL preview renderer
- optional PostgreSQL persistence preview builder

It does not call a repository, execute SQL, write records, run migrations, or make HTTP calls.

## Related Documents

- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Local Dry-Run Troubleshooting](local-dry-run-troubleshooting.md)
- [Local Parser File Content Loader Boundary](local-parser-file-content-loader-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [PostgreSQL Persistence Preview Boundary](postgresql-persistence-preview-boundary.md)
- [Public Safety](public-safety.md)
