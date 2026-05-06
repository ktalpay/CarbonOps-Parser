# Local Dry-Run CLI Boundary

This document defines the local dry-run CLI boundary.

It is a command entry path only. It accepts an explicit local DEFRA/DESNZ fixture file path and calls `run_local_file_normalized_persistence_dry_run()`. It does not connect to PostgreSQL, write to a database, execute SQL, run migrations, perform HTTP or network calls, scan directories, load configuration files, trigger source acquisition, schedule work, or use credentials.

## Command

Module invocation:

```bash
python -m carbonfactor_parser.cli local-dry-run \
  --local-path ./fixtures/defra_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-fixture \
  --content-type text/csv \
  --format-hint csv
```

Console script:

```bash
carbonops-parser local-dry-run \
  --local-path ./fixtures/defra_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-fixture \
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
  --local-path ./fixtures/defra_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-fixture \
  --format-hint csv \
  --output-format json
```

JSON output includes intermediate status fields and DDL preview text as metadata. The DDL preview is not executed.

## Exit Codes

The command returns:

- `0` for `success`
- non-zero for `failed`, `unsupported`, and `no_records`
- `2` for argument errors from the CLI parser

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

It does not call a repository, execute SQL, write records, run migrations, or make HTTP calls.

## Related Documents

- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Local Parser File Content Loader Boundary](local-parser-file-content-loader-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Normalized Result Persistence Boundary](normalized-result-persistence-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [Public Safety](public-safety.md)
