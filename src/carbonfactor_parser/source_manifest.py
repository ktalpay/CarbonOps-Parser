"""Artificial-only source manifest metadata shape."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ArtificialSourceManifestMetadata:
    """Static artificial manifest metadata for boundary-safe tests."""

    manifest_id: str
    source_family: str
    dataset_name: str
    version_label: str
    record_count: int
    generated_by: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty_string("manifest_id", self.manifest_id)
        _require_non_empty_string("source_family", self.source_family)
        _require_non_empty_string("dataset_name", self.dataset_name)
        _require_non_empty_string("version_label", self.version_label)
        _require_non_negative_integer("record_count", self.record_count)
        _require_optional_non_empty_string("generated_by", self.generated_by)
        object.__setattr__(self, "notes", _normalize_notes(self.notes))


@dataclass(frozen=True)
class ArtificialSourceManifestValidationSummary:
    """Artificial-only source manifest validation summary shape."""

    manifest_id: str
    source_family: str
    dataset_name: str
    issue_count: int
    is_valid: bool

    def __post_init__(self) -> None:
        _require_non_empty_string("manifest_id", self.manifest_id)
        _require_non_empty_string("source_family", self.source_family)
        _require_non_empty_string("dataset_name", self.dataset_name)
        _require_non_negative_integer("issue_count", self.issue_count)

    @classmethod
    def from_metadata(
        cls,
        metadata: ArtificialSourceManifestMetadata,
        issue_count: int,
    ) -> "ArtificialSourceManifestValidationSummary":
        """Create a summary from artificial metadata without loading manifests."""

        if not isinstance(metadata, ArtificialSourceManifestMetadata):
            raise TypeError("metadata must be an ArtificialSourceManifestMetadata.")

        _require_non_negative_integer("issue_count", issue_count)

        return cls(
            manifest_id=metadata.manifest_id,
            source_family=metadata.source_family,
            dataset_name=metadata.dataset_name,
            issue_count=issue_count,
            is_valid=issue_count == 0,
        )


def _require_non_empty_string(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_optional_non_empty_string(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return

    _require_non_empty_string(field_name, value)


def _require_non_negative_integer(field_name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer.")


def _normalize_notes(notes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(notes, str):
        raise ValueError("notes must be an iterable of non-empty strings.")

    try:
        normalized_notes = tuple(notes)
    except TypeError as exc:
        raise ValueError("notes must be an iterable of non-empty strings.") from exc

    for note in normalized_notes:
        _require_non_empty_string("notes", note)

    return normalized_notes


__all__ = (
    "ArtificialSourceManifestMetadata",
    "ArtificialSourceManifestValidationSummary",
)
