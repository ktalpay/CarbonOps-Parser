# Local Dry-Run Troubleshooting

This guide documents expected local dry-run failure scenarios for `carbonops-parser local-dry-run`.

These failures are local file loading, dry-run validation, parser fixture, or normalization fixture boundary outcomes. They do not write to a database, execute SQL, run migrations, make HTTP or network calls, trigger source acquisition, load configuration files, schedule work, or use credentials.

The local dry-run is not production DEFRA/DESNZ correctness validation. It only exercises the checked-in minimal fixture path and the current local/in-memory boundaries.

## Missing Or Blank Local Path

If `--local-path` is omitted, argparse rejects the command before the dry-run pipeline starts:

```bash
carbonops-parser local-dry-run \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --format-hint csv
```

Expected high-level outcome:

```text
exit_code=2
error=the following arguments are required: --local-path
```

If an empty value is supplied by a shell wrapper, the loader reports a local path validation failure before parsing, normalization, or persistence input building.

## Nonexistent File

Use an explicit local path that does not exist:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/missing_defra_desnz.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-missing-fixture \
  --content-type text/csv \
  --format-hint csv
```

Expected high-level text output:

```text
status=failed
parsed_record_count=None
normalization_record_count=None
persistence_input_record_count=None
ddl_preview_present=False
issue_count=1
load | error | PARSER_FILE_CONTENT_LOAD_NOT_FOUND | local_path must point to an existing local file.
```

No parser, normalization mapper, persistence input builder, repository, SQL, or network step is reached.

## Directory Instead Of File

If `--local-path` points at a directory, the loader returns a structured failure:

```text
status=failed
issue_stage=load
issue_code=PARSER_FILE_CONTENT_LOAD_DIRECTORY
```

The dry-run requires a regular local file. It does not scan directories or auto-discover fixture files.

## Invalid UTF-8 Or Binary-Like Content

The local loader accepts UTF-8 text only.

Invalid UTF-8 bytes return:

```text
status=unsupported
issue_stage=load
issue_code=PARSER_FILE_CONTENT_LOAD_UNSUPPORTED_ENCODING
```

UTF-8 text containing NUL bytes returns:

```text
status=unsupported
issue_stage=load
issue_code=PARSER_FILE_CONTENT_LOAD_BINARY_CONTENT
```

These outcomes stop before parser, normalization, persistence input, DDL preview, DB, SQL, or network behavior.

## Invalid Parser Header Or Content

The minimal DEFRA/DESNZ parser path expects exactly:

```text
factor_id,factor_name,unit
```

Example invalid header:

```bash
printf 'wrong,header\n1,Electricity\n' > /tmp/defra-invalid-header.csv
carbonops-parser local-dry-run \
  --local-path /tmp/defra-invalid-header.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-invalid-header \
  --format-hint csv
```

Expected high-level text output:

```text
status=failed
parsed_record_count=0
persistence_input_record_count=None
ddl_preview_present=False
issue_count=1
parse | error | DEFRA_DESNZ_CONTENT_INVALID_HEADER | DEFRA/DESNZ minimal content header must be factor_id,factor_name,unit.
```

This is a fixture parser boundary failure, not a database, SQL, network, or source acquisition failure.

## Missing Required Normalization Field

Rows that parse but leave a required raw field blank fail at the minimal normalization mapping boundary.

Example:

```bash
printf 'factor_id,factor_name,unit\n,Electricity,kWh\n' > /tmp/defra-missing-factor-id.csv
carbonops-parser local-dry-run \
  --local-path /tmp/defra-missing-factor-id.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-missing-factor-id \
  --format-hint csv
```

Expected high-level text output:

```text
status=failed
parsed_record_count=1
normalization_record_count=0
persistence_input_record_count=None
ddl_preview_present=False
issue_count=1
normalization_mapping | error | DEFRA_DESNZ_NORMALIZATION_MISSING_RAW_FIELD | DEFRA/DESNZ minimal normalization input is missing required raw field: factor_id.
```

The dry-run does not infer replacement values, convert units, classify categories, or validate real DEFRA/DESNZ correctness.

## No Records

A file with only the supported header and no data rows returns a no-record outcome:

```text
status=no_records
parsed_record_count=0
persistence_input_record_count=None
ddl_preview_present=False
issue_stage=parse
issue_code=DEFRA_DESNZ_CONTENT_NO_RECORDS
```

`no_records` is non-success for the CLI. It does not produce ready persistence input.

## Unsupported Outcomes

Unsupported outcomes currently come from local file loading boundaries such as invalid UTF-8, binary-like text, or size guard failures. They are non-success CLI outcomes and stop before parser, normalization, persistence input, DDL preview, DB, SQL, or network behavior.

## Related Documents

- [Local Dry-Run CLI Boundary](local-dry-run-cli-boundary.md)
- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Local Parser File Content Loader Boundary](local-parser-file-content-loader-boundary.md)
- [DEFRA/DESNZ Minimal Normalization Mapping Boundary](defra-desnz-minimal-normalization-mapping-boundary.md)
- [Public Safety](public-safety.md)
