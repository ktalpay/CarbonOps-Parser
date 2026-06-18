# Examples

This directory contains deterministic, local-only examples for CarbonOps-Parser. They are intended for reviewers who want to inspect carbon accounting source ingestion boundaries, parser handoffs, normalization summaries, validation issues, and PostgreSQL preview metadata without making network calls or connecting to a database.

## Fixture Quickstart Entry Point

The current public quickstart fixture is:

- [fixtures/defra_desnz_minimal.csv](fixtures/defra_desnz_minimal.csv) - a minimal DEFRA/DESNZ-style CSV fixture used by the local dry-run CLI in the repository README.

Run it from the repository root after installing the package in editable mode:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
```

This command is a non-destructive dry run. It does not download source files, call GHG Protocol, DEFRA/DESNZ, or IPCC EFDB endpoints, connect to PostgreSQL, execute SQL, write records, or make production carbon emissions correctness claims.

## Example Categories

| Category | Files | Purpose |
| --- | --- | --- |
| Parser and fixture flow | `defra_desnz_parser_usage_example.py`, `fixture_parser_pipeline_example.py`, `example_in_memory_parser_usage.py`, `parser_result_contract_example.py` | Show local parser contracts and fixture-oriented parser behavior. |
| Source acquisition handoff | `example_acquisition_artifact_parser_input_mapping.py`, `local_source_fixture_discovery_example.py`, `parser_input_mapping_example.py` | Show how already-known local source metadata can be mapped toward parser input boundaries. |
| Normalization and summaries | `normalization_contract_example.py`, `parser_normalization_handoff_example.py`, `example_normalization_result_summary_usage.py`, `example_artificial_normalization_executor_usage.py`, `example_artificial_normalization_summary_builder_usage.py` | Show deterministic normalization and summary contracts. |
| Source adapter contracts | `source_adapter_registry_example.py`, `source_adapter_static_configuration_example.py`, `source_adapter_summary_example.py` | Show source adapter registry and metadata helpers. |
| Artificial examples | `example_artificial_fixture_parser_usage.py`, `example_artificial_in_memory_manifest_usage.py`, `example_artificial_source_acquisition_validation_pipeline.py` | Exercise artificial or placeholder source shapes for tests and documentation. These are explicitly not real source integrations. |

## Placeholder Policy

Future examples may add GHG Protocol, DEFRA/DESNZ, or IPCC EFDB slices only when a task explicitly scopes them and includes deterministic local fixtures. Placeholder examples must be labelled as placeholders and must not imply live source support, production carbon accounting correctness, compliance correctness, legal correctness, source-owner correctness, or factor correctness.
