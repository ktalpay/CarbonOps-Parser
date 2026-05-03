# CarbonOps-Parser

![CarbonOps-Parser banner](docs/assets/carbonops-parser-banner.svg)

Scheduled carbon factor ingestion and parsing reference project with Python and .NET implementation options.

![Status](https://img.shields.io/badge/status-documentation%20baseline-2f6f88)
![Phase](https://img.shields.io/badge/phase-Phase%201%20ingestion-4f7cac)
![Python](https://img.shields.io/badge/Python-planned-3776ab)
![.NET](https://img.shields.io/badge/.NET-planned-512bd4)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Phase%201-336791)
![Docs](https://img.shields.io/badge/docs-in%20progress-5c7cfa)
![Release](https://img.shields.io/badge/release-not%20published%20yet-lightgrey)
![CI](https://img.shields.io/badge/CI-not%20configured%20yet-lightgrey)
![Package](https://img.shields.io/badge/package-not%20published%20yet-lightgrey)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

CarbonOps-Parser is a standalone public technical project for scheduled carbon factor source ingestion and parsing. It checks selected public emission factor sources, detects source version or hash changes, archives raw source files, parses source-specific structures, validates parsed records, and stores ingestion metadata and source-specific records in PostgreSQL.

The project is independent from `carbonops-assistant`. It is not a continuation, module, plugin, or dependency of that project.

## Current Status

CarbonOps-Parser is in early Phase 1. The repository currently emphasizes project documentation, architecture, schema contract notes, source support planning, and public contribution structure before parser implementation begins.

Implementation work is planned for two independent paths:

- Python in `src/python`
- .NET in `src/dotnet`

Users who clone or fork the repository should be able to choose either implementation path.

## Phase 1 Scope

Phase 1 focuses on scheduled ingestion and parsing for:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

The intended Phase 1 workflow is:

1. Read configuration.
2. Validate the database provider.
3. Connect to PostgreSQL.
4. Check whether required tables exist.
5. Create missing tables if needed.
6. Initialize source schedules.
7. Check source version and file hash.
8. Download a source document when a new version or hash is detected.
9. Archive the raw source file.
10. Parse source-specific structures.
11. Validate parsed records.
12. Persist shared ingestion metadata and source-specific records.
13. Store import summaries and validation issues.

## Architecture At A Glance

```text
source schedule
  -> version/hash check
  -> download when changed
  -> raw file archive
  -> source-specific parser
  -> validation
  -> PostgreSQL persistence
  -> import summary and validation issues
```

Phase 1 uses shared ingestion metadata tables plus source-specific master/detail tables. It does not force GHG Protocol, DEFRA/DESNZ, and IPCC EFDB into one canonical factor table. A normalized or search-oriented projection may be considered in a later phase.

## Implementation Options

### Python

The Python implementation is planned first because it is practical for source discovery, spreadsheet inspection, parser mapping, validation, and data engineering workflows.

The initial Python source adapter contracts and in-memory registry live under `src/carbonfactor_parser/source_adapters`.

See [src/python/README.md](src/python/README.md).

### .NET

The .NET implementation is planned as an independent Worker Service path that follows the same conceptual workflow with .NET-oriented application structure.

See [src/dotnet/README.md](src/dotnet/README.md).

## Developer Tests

Run the lightweight Python test suite from the repository root:

```bash
python -m pytest
```

Pytest configuration is kept in [pyproject.toml](pyproject.toml), including the `src` package import path used by the tests.

## Public API Examples

The `carbonfactor_parser.source_adapters` package exposes source adapter contracts and lightweight helpers for tests, prototypes, and implementation slices.

Hash source content without reading or downloading files:

```python
from carbonfactor_parser.source_adapters import (
    sha256_hex_from_bytes,
    sha256_hex_from_text,
)

content_hash = sha256_hex_from_bytes(b"sample source content")
note_hash = sha256_hex_from_text("sample metadata note")
```

Create and validate metadata for an existing local file:

```python
from pathlib import Path

from carbonfactor_parser.source_adapters import (
    SourceFamily,
    build_source_document_from_file,
    validate_source_document_metadata,
)

document = build_source_document_from_file(
    source_family=SourceFamily.DEFRA_DESNZ,
    source_name="Example local factor file",
    file_path=Path("data/raw/example/source.csv"),
)

metadata_issues = validate_source_document_metadata(document)
```

Create and validate an ingestion summary contract:

```python
from carbonfactor_parser.source_adapters import (
    SourceFamily,
    create_ingestion_run_summary,
    validate_ingestion_run_summary,
)

summary = create_ingestion_run_summary(
    ingestion_id="example-run-001",
    source_family=SourceFamily.DEFRA_DESNZ,
    source_name="Example local factor file",
)

summary_issues = validate_ingestion_run_summary(summary)
```

## Source Support

Each Phase 1 source family will have its own schedule, source version/hash check, parser, validation rules, archive layout, and source-specific tables.

| Source family | Phase 1 role | Table group |
| --- | --- | --- |
| GHG Protocol | Source-specific parser and workbook/tool mapping | `ghg_*` |
| DEFRA/DESNZ | First planned ingestion slice after discovery | `defra_*` |
| IPCC EFDB | Heterogeneous source discovery and parser mapping | `ipcc_*` |

See [docs/source-support.md](docs/source-support.md) and [docs/source-discovery.md](docs/source-discovery.md).

## Configuration Summary

The conceptual configuration model includes:

- Database provider and connection settings.
- Raw archive path.
- Source-specific enabled flags.
- Source-specific schedules with day, week, month, time, and timezone support.

Phase 1 implements only `postgres` as the database provider. `mysql` and `mssql` are recognized as conceptual provider names but are not implemented in Phase 1.

See [docs/configuration-model.md](docs/configuration-model.md).

The shared conceptual example lives at [config/carbonops.config.example.yaml](config/carbonops.config.example.yaml).

## Database Model Summary

PostgreSQL is the Phase 1 persistence target. The model includes:

- Shared ingestion metadata tables: `carbon_sources`, `carbon_source_versions`, `carbon_import_runs`, `carbon_raw_files`, `carbon_validation_issues`, and `carbon_job_locks`.
- DEFRA/DESNZ tables: `defra_categories`, `defra_subcategories`, `defra_factor_sets`, and `defra_factor_values`.
- GHG Protocol tables: `ghg_tools`, `ghg_factor_sheets`, `ghg_factor_groups`, and `ghg_factor_values`.
- IPCC EFDB tables: `ipcc_sectors`, `ipcc_categories`, `ipcc_references`, `ipcc_factor_records`, and `ipcc_factor_values`.

See [docs/database-model.md](docs/database-model.md), [docs/database-startup.md](docs/database-startup.md), and [database/postgres/README.md](database/postgres/README.md).

## Documentation Map

- [Architecture](docs/architecture.md)
- [Configuration Model](docs/configuration-model.md)
- [Configuration Example](config/carbonops.config.example.yaml)
- [Background Job Model](docs/background-job-model.md)
- [Database Model](docs/database-model.md)
- [Database Startup](docs/database-startup.md)
- [Ingestion Metadata Model](docs/ingestion-metadata-model.md)
- [Codex-Assisted Runs](docs/codex-runs/README.md)
- [Engineering Standards](docs/engineering-standards.md)
- [Linux Service Setup](docs/linux-service-setup.md)
- [Source Support](docs/source-support.md)
- [Source Discovery](docs/source-discovery.md)
- [Source Ingestion Boundaries](docs/source-ingestion-boundaries.md)
- [Source Adapter Contract](docs/source-adapter-contract.md)
- [Source Adapter Execution Flow](docs/source-adapter-execution-flow.md)
- [Source Adapter Error And Warning Handling](docs/source-adapter-error-warning-handling.md)
- [Source Adapter Configuration Boundaries](docs/source-adapter-configuration-boundaries.md)
- [Source-Specific Adapter Skeleton Guidance](docs/source-specific-adapter-skeleton-guidance.md)
- [DEFRA/DESNZ Adapter Skeleton Boundaries](docs/defra-desnz-adapter-skeleton-boundaries.md)
- [Parser Handoff Boundary](docs/parser-handoff-boundary.md)
- [Parser Contract Boundaries](docs/parser-contract-boundaries.md)
- [Source-Specific Parser Skeleton Boundaries](docs/source-specific-parser-skeleton-boundaries.md)
- [Source Adapter Package Recap](docs/source-adapter-package-recap.md)
- [Roadmap](docs/roadmap.md)
- [Task Breakdown](docs/task-breakdown.md)
- [Limitations](docs/limitations.md)
- [Public Safety](docs/public-safety.md)
- [PostgreSQL Database Notes](database/postgres/README.md)

## Roadmap Summary

Near-term work moves from documentation polish to schema scripts, Python source discovery, PostgreSQL startup checks, raw archive handling, and the first DEFRA/DESNZ ingestion slice. The .NET Worker Service path follows as an independent implementation option.

See [docs/roadmap.md](docs/roadmap.md) and [docs/task-breakdown.md](docs/task-breakdown.md).

## Governance

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)
- [Issue templates](.github/ISSUE_TEMPLATE)
- [Pull request template](.github/pull_request_template.md)
- [CI placeholder](.github/workflows/README.md)

Issues and pull requests are welcome for documentation, examples, parser mappings, source discovery, database schema notes, and implementation improvements.

## Non-Goals

CarbonOps-Parser does not:

- Calculate carbon inventories.
- Produce emissions reports.
- Replace source-owner documentation or source files.
- Guarantee source data correctness.
- Provide a deployment platform.
- Normalize all source families into one shared factor table during Phase 1.

## License

CarbonOps-Parser is licensed under the [Apache License 2.0](LICENSE).
