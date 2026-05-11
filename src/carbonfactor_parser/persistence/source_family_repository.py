"""Runtime-passive source-family master/detail repository contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    get_source_family_table_names,
)


class SourceFamilyRepositoryPersistStatus(str, Enum):
    """Deterministic metadata-only source-family persist status values."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"


@dataclass(frozen=True)
class SourceFamilyMasterRecord:
    """Runtime-passive source-family master record contract."""

    source_family: SourceFamily
    source_family_master_id: str
    source_document_id: str
    master_external_key: str
    lifecycle_status: str
    effective_from: str | None
    effective_to: str | None
    record_checksum_sha256: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SourceFamilyDetailRecord:
    """Runtime-passive source-family detail record contract."""

    source_family: SourceFamily
    source_family_detail_id: str
    source_family_master_id: str
    detail_external_key: str
    factor_value: str
    factor_unit: str
    lifecycle_status: str
    record_checksum_sha256: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SourceFamilyRepositoryIssue:
    """Metadata-only source-family repository contract issue."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceFamilyRepositoryPersistResult:
    """Metadata-only source-family master/detail repository persist result."""

    provider_name: str
    status: SourceFamilyRepositoryPersistStatus
    persisted_master_count: int
    persisted_detail_count: int
    issues: tuple[SourceFamilyRepositoryIssue, ...] = ()


@runtime_checkable
class SourceFamilyRepository(Protocol):
    """Protocol for metadata-only source-family master/detail repositories."""

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""

    def persist_source_family_records(
        self,
        master_records: tuple[SourceFamilyMasterRecord, ...],
        detail_records: tuple[SourceFamilyDetailRecord, ...],
    ) -> SourceFamilyRepositoryPersistResult:
        """Persist source-family master/detail records without side effects."""


def create_source_family_repository_persist_result(
    *,
    provider_name: str,
    master_records: (
        tuple[SourceFamilyMasterRecord, ...] | list[SourceFamilyMasterRecord]
    ),
    detail_records: (
        tuple[SourceFamilyDetailRecord, ...] | list[SourceFamilyDetailRecord]
    ),
    issues: tuple[SourceFamilyRepositoryIssue, ...]
    | list[SourceFamilyRepositoryIssue] = (),
) -> SourceFamilyRepositoryPersistResult:
    """Create deterministic metadata-only source-family persist result."""

    master_snapshot = tuple(master_records)
    detail_snapshot = tuple(detail_records)
    validation_issues = list(
        validate_source_family_repository_inputs(
            provider_name=provider_name,
            master_records=master_snapshot,
            detail_records=detail_snapshot,
        ).issues,
    )
    validation_issues.extend(issues)

    status = (
        SourceFamilyRepositoryPersistStatus.FAILED_VALIDATION
        if validation_issues
        else SourceFamilyRepositoryPersistStatus.DECLARED
    )

    return SourceFamilyRepositoryPersistResult(
        provider_name=provider_name,
        status=status,
        persisted_master_count=0 if validation_issues else len(master_snapshot),
        persisted_detail_count=0 if validation_issues else len(detail_snapshot),
        issues=tuple(validation_issues),
    )


@dataclass(frozen=True)
class SourceFamilyRepositoryValidationResult:
    """Validation result for source-family repository metadata."""

    issues: tuple[SourceFamilyRepositoryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_source_family_repository_inputs(
    *,
    provider_name: str,
    master_records: tuple[SourceFamilyMasterRecord, ...],
    detail_records: tuple[SourceFamilyDetailRecord, ...],
) -> SourceFamilyRepositoryValidationResult:
    """Validate source-family repository inputs without runtime side effects."""

    issues: list[SourceFamilyRepositoryIssue] = []

    if not isinstance(provider_name, str) or not provider_name.strip():
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_MISSING_PROVIDER_NAME",
                message="provider_name must be a non-empty string.",
                field_name="provider_name",
            ),
        )

    master_keys: set[tuple[SourceFamily, str]] = set()
    for index, record in enumerate(master_records):
        if not isinstance(record, SourceFamilyMasterRecord):
            issues.append(
                SourceFamilyRepositoryIssue(
                    code="SOURCE_FAMILY_REPOSITORY_INVALID_MASTER_RECORD",
                    message=(
                        "master_records must contain SourceFamilyMasterRecord "
                        "instances."
                    ),
                    field_name=f"master_records[{index}]",
                ),
            )
            continue

        source_family = _validate_record_source_family(
            record.source_family,
            f"master_records[{index}].source_family",
            issues,
        )
        _validate_master_record(record, index, issues)
        if _is_non_empty_string(record.source_family_master_id):
            if source_family is not None:
                master_keys.add((source_family, record.source_family_master_id))

    for index, record in enumerate(detail_records):
        if not isinstance(record, SourceFamilyDetailRecord):
            issues.append(
                SourceFamilyRepositoryIssue(
                    code="SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_RECORD",
                    message=(
                        "detail_records must contain SourceFamilyDetailRecord "
                        "instances."
                    ),
                    field_name=f"detail_records[{index}]",
                ),
            )
            continue

        _validate_detail_record(record, index, master_keys, issues)

    return SourceFamilyRepositoryValidationResult(issues=tuple(issues))


def source_family_repository_table_names(
    source_family: SourceFamily | str,
) -> tuple[str, str]:
    """Return the master/detail table names owned by a source family."""

    table_names = get_source_family_table_names(source_family)
    return table_names[0], table_names[1]


def _validate_master_record(
    record: SourceFamilyMasterRecord,
    index: int,
    issues: list[SourceFamilyRepositoryIssue],
) -> None:
    for field_name in (
        "source_family_master_id",
        "source_document_id",
        "master_external_key",
        "lifecycle_status",
        "record_checksum_sha256",
        "created_at",
        "updated_at",
    ):
        _append_required_string_issue(
            issues,
            getattr(record, field_name),
            f"master_records[{index}].{field_name}",
        )


def _validate_detail_record(
    record: SourceFamilyDetailRecord,
    index: int,
    master_keys: set[tuple[SourceFamily, str]],
    issues: list[SourceFamilyRepositoryIssue],
) -> None:
    source_family = _validate_record_source_family(
        record.source_family,
        f"detail_records[{index}].source_family",
        issues,
    )

    for field_name in (
        "source_family_detail_id",
        "source_family_master_id",
        "detail_external_key",
        "factor_value",
        "factor_unit",
        "lifecycle_status",
        "record_checksum_sha256",
        "created_at",
        "updated_at",
    ):
        _append_required_string_issue(
            issues,
            getattr(record, field_name),
            f"detail_records[{index}].{field_name}",
        )

    if (
        source_family is not None
        and _is_non_empty_string(record.source_family_master_id)
        and (source_family, record.source_family_master_id) not in master_keys
    ):
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED",
                message=(
                    "detail record source_family_master_id must reference a "
                    "declared master record for the same source family."
                ),
                field_name=f"detail_records[{index}].source_family_master_id",
            ),
        )


def _validate_record_source_family(
    value: object,
    field_name: str,
    issues: list[SourceFamilyRepositoryIssue],
) -> SourceFamily | None:
    try:
        return SourceFamily(value)
    except (TypeError, ValueError):
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_INVALID_SOURCE_FAMILY",
                message="source_family must be a supported Phase 1 source family.",
                field_name=field_name,
            ),
        )
        return None


def _append_required_string_issue(
    issues: list[SourceFamilyRepositoryIssue],
    value: object,
    field_name: str,
) -> None:
    if not _is_non_empty_string(value):
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_MISSING_REQUIRED_FIELD",
                message="required fields must be non-empty strings.",
                field_name=field_name,
            ),
        )


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
