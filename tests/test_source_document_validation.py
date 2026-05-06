from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from carbonfactor_parser.source_adapters import (
    SourceDocument,
    SourceFamily,
    validate_source_document_metadata,
)


VALID_HASH = "a" * 64


def valid_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local source",
        source_url="https://example.invalid/source.xlsx",
        file_reference="data/raw/defra/source.xlsx",
        source_version="2026",
        publication_date=date(2026, 1, 1),
        retrieved_at=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
        content_hash=VALID_HASH,
    )


def test_valid_source_document_returns_no_issues() -> None:
    assert validate_source_document_metadata(valid_document()) == []


def test_missing_source_family_is_reported() -> None:
    document = replace(valid_document(), source_family=None)  # type: ignore[arg-type]

    assert validate_source_document_metadata(document) == [
        "source_family must be present.",
    ]


def test_blank_source_name_is_reported() -> None:
    document = replace(valid_document(), source_name="  ")

    assert validate_source_document_metadata(document) == [
        "source_name must be a non-empty string.",
    ]


def test_missing_source_url_and_file_reference_is_reported() -> None:
    document = replace(valid_document(), source_url=None, file_reference=None)

    assert validate_source_document_metadata(document) == [
        "at least one of source_url or file_reference must be a non-empty string.",
    ]


def test_blank_source_url_and_file_reference_are_treated_as_missing() -> None:
    document = replace(valid_document(), source_url="  ", file_reference="")

    assert validate_source_document_metadata(document) == [
        "at least one of source_url or file_reference must be a non-empty string.",
    ]


def test_invalid_optional_field_types_are_reported() -> None:
    document = replace(
        valid_document(),
        source_url=123,  # type: ignore[arg-type]
        file_reference=object(),  # type: ignore[arg-type]
        source_version=2026,  # type: ignore[arg-type]
        publication_date=datetime(2026, 1, 1, 12, 0),  # type: ignore[arg-type]
        retrieved_at="2026-05-03T12:00:00Z",  # type: ignore[arg-type]
        content_hash=123,  # type: ignore[arg-type]
    )

    assert validate_source_document_metadata(document) == [
        "at least one of source_url or file_reference must be a non-empty string.",
        "source_url must be a string when present.",
        "file_reference must be a string when present.",
        "source_version must be a string when present.",
        "publication_date must be a date when present.",
        "retrieved_at must be a datetime when present.",
        "content_hash must be a string when present.",
    ]


@pytest.mark.parametrize(
    "content_hash",
    [
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
    ],
)
def test_invalid_content_hash_format_is_reported(content_hash: str) -> None:
    document = replace(valid_document(), content_hash=content_hash)

    assert validate_source_document_metadata(document) == [
        "content_hash must be a lowercase 64-character hexadecimal string.",
    ]


def test_naive_retrieved_at_is_reported() -> None:
    document = replace(valid_document(), retrieved_at=datetime(2026, 5, 3, 12, 0))

    assert validate_source_document_metadata(document) == [
        "retrieved_at must be timezone-aware when present.",
    ]


def test_non_source_document_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="document must be a SourceDocument."):
        validate_source_document_metadata(object())  # type: ignore[arg-type]


def test_issue_ordering_is_deterministic() -> None:
    document = SourceDocument(
        source_family=None,  # type: ignore[arg-type]
        source_name=" ",
        source_url=None,
        file_reference=None,
        source_version=2026,  # type: ignore[arg-type]
        publication_date="2026-01-01",  # type: ignore[arg-type]
        retrieved_at=datetime(2026, 5, 3, 12, 0),
        content_hash="A" * 64,
    )

    assert validate_source_document_metadata(document) == [
        "source_family must be present.",
        "source_name must be a non-empty string.",
        "at least one of source_url or file_reference must be a non-empty string.",
        "source_version must be a string when present.",
        "publication_date must be a date when present.",
        "retrieved_at must be timezone-aware when present.",
        "content_hash must be a lowercase 64-character hexadecimal string.",
    ]


def test_file_paths_are_not_checked_for_existence() -> None:
    document = replace(
        valid_document(),
        source_url=None,
        file_reference="/path/that/does/not/exist/source.xlsx",
    )

    assert validate_source_document_metadata(document) == []


def test_urls_are_not_checked_for_reachability() -> None:
    document = replace(
        valid_document(),
        source_url="https://example.invalid/not-checked.xlsx",
        file_reference=None,
    )

    assert validate_source_document_metadata(document) == []
