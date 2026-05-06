"""Status constants and deterministic helpers for source acquisition results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from carbonfactor_parser.source_acquisition.client import SourceAcquisitionResult


ACQUISITION_STATUS_ACQUIRED = "acquired"
ACQUISITION_STATUS_FAILED = "failed"
ACQUISITION_STATUS_SKIPPED = "skipped"
ACQUISITION_STATUS_NOT_IMPLEMENTED = "not_implemented"

ACQUISITION_SUCCESS_STATUSES = frozenset({ACQUISITION_STATUS_ACQUIRED})
ACQUISITION_FAILED_STATUSES = frozenset({ACQUISITION_STATUS_FAILED})
ACQUISITION_SKIPPED_STATUSES = frozenset(
    {ACQUISITION_STATUS_SKIPPED, ACQUISITION_STATUS_NOT_IMPLEMENTED}
)
ACQUISITION_KNOWN_STATUSES = frozenset(
    ACQUISITION_SUCCESS_STATUSES
    | ACQUISITION_FAILED_STATUSES
    | ACQUISITION_SKIPPED_STATUSES
)


def is_acquired_status(status: str) -> bool:
    """Return True when status represents successful acquisition."""

    return status in ACQUISITION_SUCCESS_STATUSES


def is_failed_status(status: str) -> bool:
    """Return True when status represents a failed acquisition."""

    return status in ACQUISITION_FAILED_STATUSES


def is_skipped_status(status: str) -> bool:
    """Return True when status represents a skipped acquisition."""

    return status in ACQUISITION_SKIPPED_STATUSES


def count_acquisition_statuses(
    results: Iterable["SourceAcquisitionResult"],
) -> tuple[int, int, int]:
    """Count acquired, failed, and skipped outcomes in deterministic order."""

    acquired_count = 0
    failed_count = 0
    skipped_count = 0

    for result in results:
        if is_acquired_status(result.status):
            acquired_count += 1
        elif is_failed_status(result.status):
            failed_count += 1
        elif is_skipped_status(result.status):
            skipped_count += 1

    return acquired_count, failed_count, skipped_count
