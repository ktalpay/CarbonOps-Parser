"""Source adapter summary helper example."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from carbonfactor_parser.source_adapters import (
    LocalFileSourceAdapter,
    SourceFamily,
    summarize_source_adapter_result,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
)


def build_source_adapter_summary_example(
    *,
    fixture_directory: str | Path = FIXTURE_DIRECTORY,
    allowed_extensions: Iterable[str] | str | None = (".csv", ".json"),
) -> dict[str, object]:
    discovery_result = LocalFileSourceAdapter(
        directory_path=fixture_directory,
        source_family=SourceFamily.GHG_PROTOCOL,
        allowed_extensions=allowed_extensions,
    ).discover()
    summary = summarize_source_adapter_result(discovery_result)

    return {
        "document_count": summary.document_count,
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "has_documents": summary.has_documents,
        "has_warnings": summary.has_warnings,
        "has_errors": summary.has_errors,
        "is_clean": summary.is_clean,
        "source_families": tuple(family.value for family in summary.source_families),
        "source_names": summary.source_names,
        "file_extensions": summary.file_extensions,
    }
