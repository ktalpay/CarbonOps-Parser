"""Artificial normalization result summary model."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, init=False)
class NormalizationResultSummary:
    """Artificial output-shape summary contract for normalization results."""

    record_count: int
    issue_count: int
    source_family: str | None
    source_id: str | None
    is_artificial: bool
    metadata: Mapping[str, str]
    warning_count: int
    error_count: int

    def __init__(
        self,
        record_count: int | None = None,
        issue_count: int | None = None,
        source_family: str | None = None,
        source_id: str | None = None,
        is_artificial: bool = True,
        metadata: Mapping[str, str] | None = None,
        warning_count: int = 0,
        error_count: int = 0,
        normalized_record_count: int | None = None,
        has_normalized_records: bool | None = None,
        has_warnings: bool | None = None,
        has_errors: bool | None = None,
        is_clean: bool | None = None,
    ) -> None:
        """Create a summary without deriving data from normalization records."""

        del has_normalized_records, has_warnings, has_errors, is_clean

        resolved_record_count = (
            normalized_record_count if record_count is None else record_count
        )
        if resolved_record_count is None:
            resolved_record_count = 0

        resolved_issue_count = (
            warning_count + error_count if issue_count is None else issue_count
        )

        _require_non_negative("record_count", resolved_record_count)
        _require_non_negative("issue_count", resolved_issue_count)
        _require_non_negative("warning_count", warning_count)
        _require_non_negative("error_count", error_count)

        copied_metadata = {
            str(key): str(value) for key, value in (metadata or {}).items()
        }

        object.__setattr__(self, "record_count", resolved_record_count)
        object.__setattr__(self, "issue_count", resolved_issue_count)
        object.__setattr__(self, "source_family", source_family)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "is_artificial", is_artificial)
        object.__setattr__(self, "metadata", MappingProxyType(copied_metadata))
        object.__setattr__(self, "warning_count", warning_count)
        object.__setattr__(self, "error_count", error_count)

    @property
    def normalized_record_count(self) -> int:
        """Compatibility alias for the normalization contract count."""

        return self.record_count

    @property
    def has_normalized_records(self) -> bool:
        """Whether the summary describes any normalized records."""

        return bool(self.record_count)

    @property
    def has_warnings(self) -> bool:
        """Whether the summary describes normalization warnings."""

        return bool(self.warning_count)

    @property
    def has_errors(self) -> bool:
        """Whether the summary describes normalization errors."""

        return bool(self.error_count)

    @property
    def is_clean(self) -> bool:
        """Whether the summary describes no warning or error issues."""

        return not self.warning_count and not self.error_count


def _require_non_negative(field_name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
