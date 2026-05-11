"""Runtime-passive source document repository contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from carbonfactor_parser.source_acquisition.models import (
    SourceDocumentPersistenceRecord,
)


class SourceDocumentRepositoryPersistStatus(str, Enum):
    """Deterministic metadata-only source document persist status values."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"


@dataclass(frozen=True)
class SourceDocumentRepositoryIssue:
    """Metadata-only source document repository contract issue."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceDocumentRepositoryPersistResult:
    """Metadata-only source document repository persist result."""

    provider_name: str
    status: SourceDocumentRepositoryPersistStatus
    persisted_count: int
    issues: tuple[SourceDocumentRepositoryIssue, ...] = ()


@runtime_checkable
class SourceDocumentRepository(Protocol):
    """Protocol for metadata-only source document repositories."""

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""

    def persist_source_documents(
        self,
        records: tuple[SourceDocumentPersistenceRecord, ...],
    ) -> SourceDocumentRepositoryPersistResult:
        """Persist source document metadata contractually without side effects."""


def create_source_document_repository_persist_result(
    *,
    provider_name: str,
    records: (
        tuple[SourceDocumentPersistenceRecord, ...]
        | list[SourceDocumentPersistenceRecord]
    ),
    issues: (
        tuple[SourceDocumentRepositoryIssue, ...]
        | list[SourceDocumentRepositoryIssue]
    ) = (),
) -> SourceDocumentRepositoryPersistResult:
    """Create deterministic metadata-only source document persist result."""

    record_snapshot = tuple(records)
    validation_issues = list(
        validate_source_document_repository_inputs(
            provider_name=provider_name,
            records=record_snapshot,
        ).issues,
    )
    validation_issues.extend(issues)

    status = (
        SourceDocumentRepositoryPersistStatus.FAILED_VALIDATION
        if validation_issues
        else SourceDocumentRepositoryPersistStatus.DECLARED
    )

    return SourceDocumentRepositoryPersistResult(
        provider_name=provider_name,
        status=status,
        persisted_count=0 if validation_issues else len(record_snapshot),
        issues=tuple(validation_issues),
    )


@dataclass(frozen=True)
class SourceDocumentRepositoryValidationResult:
    """Validation result for source document repository metadata."""

    issues: tuple[SourceDocumentRepositoryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_source_document_repository_inputs(
    *,
    provider_name: str,
    records: tuple[SourceDocumentPersistenceRecord, ...],
) -> SourceDocumentRepositoryValidationResult:
    """Validate repository inputs without runtime side effects."""

    issues: list[SourceDocumentRepositoryIssue] = []

    if not isinstance(provider_name, str) or not provider_name.strip():
        issues.append(
            SourceDocumentRepositoryIssue(
                code="SOURCE_DOCUMENT_REPOSITORY_MISSING_PROVIDER_NAME",
                message="provider_name must be a non-empty string.",
                field_name="provider_name",
            ),
        )

    for index, record in enumerate(records):
        if not isinstance(record, SourceDocumentPersistenceRecord):
            issues.append(
                SourceDocumentRepositoryIssue(
                    code="SOURCE_DOCUMENT_REPOSITORY_INVALID_RECORD",
                    message=(
                        "records must contain SourceDocumentPersistenceRecord "
                        "instances."
                    ),
                    field_name=f"records[{index}]",
                ),
            )

    return SourceDocumentRepositoryValidationResult(issues=tuple(issues))
