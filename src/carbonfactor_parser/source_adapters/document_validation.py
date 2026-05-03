"""Validation helpers for source document metadata."""

from __future__ import annotations

import re
from datetime import date, datetime

from carbonfactor_parser.source_adapters.contracts import SourceDocument, SourceFamily


_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def validate_source_document_metadata(document: SourceDocument) -> list[str]:
    if not isinstance(document, SourceDocument):
        raise TypeError("document must be a SourceDocument.")

    issues: list[str] = []

    if not isinstance(document.source_family, SourceFamily):
        issues.append("source_family must be present.")

    if not isinstance(document.source_name, str) or not document.source_name.strip():
        issues.append("source_name must be a non-empty string.")

    source_url_is_present = _is_present_string(document.source_url)
    file_reference_is_present = _is_present_string(document.file_reference)
    if not source_url_is_present and not file_reference_is_present:
        issues.append(
            "at least one of source_url or file_reference must be a non-empty string."
        )

    if document.source_url is not None and not isinstance(document.source_url, str):
        issues.append("source_url must be a string when present.")

    if document.file_reference is not None and not isinstance(
        document.file_reference,
        str,
    ):
        issues.append("file_reference must be a string when present.")

    if document.source_version is not None and not isinstance(
        document.source_version,
        str,
    ):
        issues.append("source_version must be a string when present.")

    if document.publication_date is not None and not isinstance(
        document.publication_date,
        date,
    ):
        issues.append("publication_date must be a date when present.")
    elif isinstance(document.publication_date, datetime):
        issues.append("publication_date must be a date when present.")

    if document.retrieved_at is not None:
        if not isinstance(document.retrieved_at, datetime):
            issues.append("retrieved_at must be a datetime when present.")
        elif document.retrieved_at.tzinfo is None:
            issues.append("retrieved_at must be timezone-aware when present.")

    if document.content_hash is not None:
        if not isinstance(document.content_hash, str):
            issues.append("content_hash must be a string when present.")
        elif not _SHA256_HEX_PATTERN.fullmatch(document.content_hash):
            issues.append(
                "content_hash must be a lowercase 64-character hexadecimal string."
            )

    return issues


def _is_present_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
