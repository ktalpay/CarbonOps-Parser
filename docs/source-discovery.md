# Source Discovery

Source discovery is required before final parser mapping because GHG Protocol, DEFRA/DESNZ, and IPCC EFDB have different document structures and metadata conventions.

Discovery should inspect source files before persistence models and parser rules are finalized.

## Discovery Goals

Discovery should collect:

- File name
- File size
- Content type
- Sheet names when the source is spreadsheet-based
- Header rows
- Column names
- Sample rows
- Detected data regions
- Potential master/detail mappings

## Python Ownership

Python should own the first source discovery tooling. It is practical for early Excel inspection, source profiling, sample extraction, and parser mapping experiments.

The discovery outputs should inform both implementation paths. The .NET implementation should not depend on Python discovery code at runtime.

## Python Source-Year Availability Contract

The packaged Python ingestion runner asks each source-family adapter for one
target year at a time. Discovery returns a structured
`source_year_available` or `no_available_source_year` result before any
download, parse, insert, or year-state update is attempted.

When discovery returns `no_available_source_year`, the runner performs a safe
no-op for that source family and year. It does not download an artifact, parse
content, insert records, or advance `source_family_year_states`.

When discovery returns `source_year_available`, the result includes a
download-ready artifact reference plus metadata such as publication URL, title,
version label, content type, format hint, and the discovery strategy used.

## Source Family Behavior

| Source family | Availability behavior | Notes |
| --- | --- | --- |
| DEFRA/DESNZ | Configured artifact URL first; otherwise GOV.UK publication page flat-file link discovery for years in the reviewed availability map. | The default map currently includes `2024` and `2025` GOV.UK publication pages. `2026` is unavailable unless an explicit `source_years.defra_desnz.2026.artifact_url` is configured or the reviewed default map is updated. |
| GHG Protocol | Explicit configured artifact URL required. | This boundary does not assume a stable public year-index for GHG Protocol artifacts. Configure `source_years.ghg_protocol.<year>.artifact_url` for local fixtures or reviewed source artifacts. |
| IPCC EFDB | Explicit configured artifact URL required. | This boundary does not assume a stable public year-index artifact contract for IPCC EFDB. Configure `source_years.ipcc_efdb.<year>.artifact_url` for local fixtures or reviewed source artifacts. |

The checked-in local ingestion example config keeps deterministic fixture
behavior for `2024`, `2025`, and `2026` across all three source families by
providing explicit `source_years` artifact entries.

## DEFRA/DESNZ GOV.UK Discovery

DEFRA/DESNZ live discovery is intentionally narrow. For a mapped target year,
the adapter reads the configured GOV.UK publication page and selects the first
link whose visible label contains `flat` and whose URL starts with
`https://assets.publishing.service.gov.uk/`.

Discovery failures return user-readable unavailable metadata with redacted
transport details. They are not treated as successful availability, and they do
not trigger download or downstream ingestion steps.

## Non-Claims

This discovery contract does not claim source-owner correctness, factor
correctness, legal correctness, compliance correctness, or production carbon
accounting correctness. It only defines conservative target-year availability
behavior for the current Python ingestion boundary.
