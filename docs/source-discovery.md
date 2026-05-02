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

## Implementation Boundary

This documentation baseline does not add parser implementation, download logic, or source discovery scripts. Those should be added in later tasks.
