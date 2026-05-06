"""Local fixture discovery example for LocalFileSourceAdapter."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from carbonfactor_parser.source_adapters import (
    LocalFileSourceAdapter,
    SourceDocument,
    SourceFamily,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
)


def discover_fixture_documents(
    *,
    fixture_directory: str | Path = FIXTURE_DIRECTORY,
    allowed_extensions: Iterable[str] | str | None = (".csv", ".json"),
) -> tuple[SourceDocument, ...]:
    adapter = LocalFileSourceAdapter(
        directory_path=fixture_directory,
        source_family=SourceFamily.GHG_PROTOCOL,
        allowed_extensions=allowed_extensions,
    )
    return tuple(adapter.discover().documents)


def fixture_document_metadata(
    *,
    fixture_directory: str | Path = FIXTURE_DIRECTORY,
    allowed_extensions: Iterable[str] | str | None = (".csv", ".json"),
) -> tuple[dict[str, str | None], ...]:
    return tuple(
        {
            "source_family": document.source_family.value,
            "source_name": document.source_name,
            "file_reference": document.file_reference,
            "extension": Path(document.file_reference or "").suffix,
        }
        for document in discover_fixture_documents(
            fixture_directory=fixture_directory,
            allowed_extensions=allowed_extensions,
        )
    )


if __name__ == "__main__":
    for metadata in fixture_document_metadata():
        print(metadata)
