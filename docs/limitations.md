# Limitations

CarbonOps-Parser is a scheduled carbon factor ingestion and parsing reference project. It has clear boundaries.

## Non-Goals

CarbonOps-Parser does not:

- Calculate carbon inventories.
- Produce emissions reports.
- Replace source owners' documentation or source files.
- Certify source data correctness.
- Provide a deployment platform.
- Guarantee that external sources are complete, current, or error-free.
- Normalize all source families into one shared factor table during Phase 1.

## Phase 1 Limits

Phase 1 is limited to:

- PostgreSQL as the implemented database provider.
- GHG Protocol, DEFRA/DESNZ, and IPCC EFDB as the supported Phase 1 source families.
- Shared ingestion metadata tables.
- Source-specific master/detail tables.
- Documentation, schema, discovery, and early ingestion slices.

The conceptual configuration model includes `mysql` and `mssql`, but those providers are not implemented in Phase 1.

## Source Data Limits

Source files are owned and maintained by their respective source organizations. CarbonOps-Parser should archive raw files and record hashes, but it does not guarantee source data correctness.

Parser mappings should be reviewed whenever source structures change.
