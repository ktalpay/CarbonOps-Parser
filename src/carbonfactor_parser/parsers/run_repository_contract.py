"""Runtime-passive repository contract for parser run results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from carbonfactor_parser.parsers.parser_run_contract import ParserRunResult


class ParserRunRepositoryPersistStatus(str, Enum):
    """Deterministic metadata-only persist status values."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"


@dataclass(frozen=True)
class ParserRunRepositoryIssue:
    """Metadata-only parser run repository contract issue."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserRunRepositoryPersistResult:
    """Metadata-only parser run repository persist result."""

    provider_name: str
    status: ParserRunRepositoryPersistStatus
    persisted_count: int
    issues: tuple[ParserRunRepositoryIssue, ...] = ()


@runtime_checkable
class ParserRunRepository(Protocol):
    """Protocol for metadata-only parser run repositories."""

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""

    def persist_runs(
        self,
        runs: tuple[ParserRunResult, ...],
    ) -> ParserRunRepositoryPersistResult:
        """Persist parser run metadata contractually without runtime side effects."""


def create_parser_run_repository_persist_result(
    *,
    provider_name: str,
    runs: tuple[ParserRunResult, ...],
    issues: tuple[ParserRunRepositoryIssue, ...] = (),
) -> ParserRunRepositoryPersistResult:
    """Create deterministic metadata-only repository persist result."""

    validation_issues = list(
        validate_parser_run_repository_inputs(
            provider_name=provider_name,
            runs=runs,
        ).issues,
    )
    validation_issues.extend(tuple(issues))

    status = (
        ParserRunRepositoryPersistStatus.FAILED_VALIDATION
        if validation_issues
        else ParserRunRepositoryPersistStatus.DECLARED
    )

    return ParserRunRepositoryPersistResult(
        provider_name=provider_name,
        status=status,
        persisted_count=0 if validation_issues else len(runs),
        issues=tuple(validation_issues),
    )


@dataclass(frozen=True)
class ParserRunRepositoryValidationResult:
    """Validation result for parser run repository metadata."""

    issues: tuple[ParserRunRepositoryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_parser_run_repository_inputs(
    *,
    provider_name: str,
    runs: tuple[ParserRunResult, ...],
) -> ParserRunRepositoryValidationResult:
    """Validate repository inputs without runtime side effects."""

    issues: list[ParserRunRepositoryIssue] = []

    if not isinstance(provider_name, str) or not provider_name.strip():
        issues.append(
            ParserRunRepositoryIssue(
                code="PARSER_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
                message="provider_name must be a non-empty string.",
                field_name="provider_name",
            ),
        )

    for index, run in enumerate(runs):
        if not isinstance(run, ParserRunResult):
            issues.append(
                ParserRunRepositoryIssue(
                    code="PARSER_RUN_REPOSITORY_INVALID_RUN",
                    message="runs must contain ParserRunResult instances.",
                    field_name=f"runs[{index}]",
                ),
            )

    return ParserRunRepositoryValidationResult(issues=tuple(issues))
