# Source Support

Phase 1 focuses on three public source families:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

Each source family has its own schedule, version/hash check, parser, validation rules, raw archive layout, and source-specific database tables.

## GHG Protocol

GHG Protocol support should use a source-specific parser and `ghg_*` tables.

Initial conceptual table group:

- `ghg_tools`
- `ghg_factor_sheets`
- `ghg_factor_groups`
- `ghg_factor_values`

## DEFRA/DESNZ

DEFRA/DESNZ support should use a source-specific parser and `defra_*` tables.

Initial conceptual table group:

- `defra_categories`
- `defra_subcategories`
- `defra_factor_sets`
- `defra_factor_values`

DEFRA/DESNZ is expected to be the first implementation slice because its source files are expected to be more structured than the other Phase 1 sources.

## IPCC EFDB

IPCC EFDB support should use a source-specific parser and `ipcc_*` tables.

Initial conceptual table group:

- `ipcc_sectors`
- `ipcc_categories`
- `ipcc_references`
- `ipcc_factor_records`
- `ipcc_factor_values`

IPCC EFDB is expected to be more heterogeneous, so final parser mapping should follow source discovery.
