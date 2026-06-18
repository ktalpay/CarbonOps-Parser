"""Runtime-passive repository contract for source acquisition run results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from carbonfactor_parser.source_acquisition.run_contract import SourceAcquisitionRunResult


class SourceAcquisitionRunRepositoryPersistStatus(str, Enum):
    """Deterministic metadata-only persist status values."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"


@dataclass(frozen=True)
class SourceAcquisitionRunRepositoryIssue:
    """Metadata-only repository contract issue."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceAcquisitionRunRepositoryPersistResult:
    """Metadata-only source acquisition run repository persist result."""

    provider_name: str
    status: SourceAcquisitionRunRepositoryPersistStatus
    persisted_count: int
    issues: tuple[SourceAcquisitionRunRepositoryIssue, ...] = ()


@runtime_checkable
class SourceAcquisitionRunRepository(Protocol):
    """Protocol for metadata-only source acquisition run repositories."""

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""

    def persist_runs(
        self,
        runs: tuple[SourceAcquisitionRunResult, ...],
    ) -> SourceAcquisitionRunRepositoryPersistResult:
        """Persist run metadata contractually without runtime side effects."""


def create_source_acquisition_run_repository_persist_result(
    *,
    provider_name: str,
    runs: tuple[SourceAcquisitionRunResult, ...],
    issues: tuple[SourceAcquisitionRunRepositoryIssue, ...] = (),
) -> SourceAcquisitionRunRepositoryPersistResult:
    """Create deterministic metadata-only repository persist result."""

    validation_issues = list(
        validate_source_acquisition_run_repository_inputs(
            provider_name=provider_name,
            runs=runs,
        ).issues,
    )
    validation_issues.extend(issues)

    status = (
        SourceAcquisitionRunRepositoryPersistStatus.FAILED_VALIDATION
        if validation_issues
        else SourceAcquisitionRunRepositoryPersistStatus.DECLARED
    )

    return SourceAcquisitionRunRepositoryPersistResult(
        provider_name=provider_name,
        status=status,
        persisted_count=0 if validation_issues else len(runs),
        issues=tuple(validation_issues),
    )


@dataclass(frozen=True)
class SourceAcquisitionRunRepositoryValidationResult:
    """Validation result for source acquisition run repository metadata."""

    issues: tuple[SourceAcquisitionRunRepositoryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_source_acquisition_run_repository_inputs(
    *,
    provider_name: str,
    runs: tuple[SourceAcquisitionRunResult, ...],
) -> SourceAcquisitionRunRepositoryValidationResult:
    """Validate repository inputs without runtime side effects."""

    issues: list[SourceAcquisitionRunRepositoryIssue] = []

    if not isinstance(provider_name, str) or not provider_name.strip():
        issues.append(
            SourceAcquisitionRunRepositoryIssue(
                code="SOURCE_ACQUISITION_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
                message="provider_name must be a non-empty string.",
                field_name="provider_name",
            ),
        )

    for index, run in enumerate(runs):
        if not isinstance(run, SourceAcquisitionRunResult):
            issues.append(
                SourceAcquisitionRunRepositoryIssue(
                    code="SOURCE_ACQUISITION_RUN_REPOSITORY_INVALID_RUN",
                    message="runs must contain SourceAcquisitionRunResult instances.",
                    field_name=f"runs[{index}]",
                ),
            )

    return SourceAcquisitionRunRepositoryValidationResult(issues=tuple(issues))
