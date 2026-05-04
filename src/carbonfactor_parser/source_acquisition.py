"""Artificial-only source acquisition metadata shape."""

from __future__ import annotations

from dataclasses import dataclass
import re


_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ArtificialSourceAcquisitionMetadata:
    """Static artificial metadata for source acquisition boundary tests.

    logical_source_name is an artificial label, not a filesystem path.
    acquired_at_label is a static label, not runtime clock behavior.
    checksum_sha256 is deterministic artificial metadata only.
    parser_hint and adapter_hint are non-authoritative hints.
    """

    source_family: str
    logical_source_name: str
    declared_content_type: str
    checksum_sha256: str
    acquired_at_label: str
    parser_hint: str | None = None
    adapter_hint: str | None = None


def create_artificial_source_acquisition_metadata(
    *,
    source_family: str,
    logical_source_name: str,
    declared_content_type: str,
    checksum_sha256: str,
    acquired_at_label: str,
    parser_hint: str | None = None,
    adapter_hint: str | None = None,
) -> ArtificialSourceAcquisitionMetadata:
    """Create artificial metadata without reading files or external state."""

    metadata = ArtificialSourceAcquisitionMetadata(
        source_family=source_family,
        logical_source_name=logical_source_name,
        declared_content_type=declared_content_type,
        checksum_sha256=checksum_sha256,
        acquired_at_label=acquired_at_label,
        parser_hint=parser_hint,
        adapter_hint=adapter_hint,
    )

    issues = validate_artificial_source_acquisition_metadata(metadata)
    if issues:
        raise ValueError("; ".join(issues))

    return metadata


def validate_artificial_source_acquisition_metadata(
    metadata: ArtificialSourceAcquisitionMetadata,
) -> list[str]:
    """Validate artificial metadata shape without source correctness claims."""

    if not isinstance(metadata, ArtificialSourceAcquisitionMetadata):
        raise TypeError(
            "metadata must be an ArtificialSourceAcquisitionMetadata.",
        )

    issues: list[str] = []

    _validate_required_string(metadata.source_family, "source_family", issues)
    _validate_required_string(
        metadata.logical_source_name,
        "logical_source_name",
        issues,
    )
    _validate_required_string(
        metadata.declared_content_type,
        "declared_content_type",
        issues,
    )
    _validate_required_string(
        metadata.checksum_sha256,
        "checksum_sha256",
        issues,
    )
    _validate_required_string(
        metadata.acquired_at_label,
        "acquired_at_label",
        issues,
    )
    _validate_optional_string(metadata.parser_hint, "parser_hint", issues)
    _validate_optional_string(metadata.adapter_hint, "adapter_hint", issues)

    if isinstance(metadata.checksum_sha256, str) and metadata.checksum_sha256.strip():
        if _SHA256_HEX_PATTERN.fullmatch(metadata.checksum_sha256) is None:
            issues.append("checksum_sha256 must look like 64 hex characters.")

    return issues


def _validate_required_string(
    value: object,
    field_name: str,
    issues: list[str],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field_name} must be a non-empty string.")


def _validate_optional_string(
    value: object,
    field_name: str,
    issues: list[str],
) -> None:
    if value is None:
        return

    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field_name} must be None or a non-empty string.")


__all__ = (
    "ArtificialSourceAcquisitionMetadata",
    "create_artificial_source_acquisition_metadata",
    "validate_artificial_source_acquisition_metadata",
)
