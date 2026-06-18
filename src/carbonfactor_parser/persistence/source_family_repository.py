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
    FAILED_DATABASE = "failed_database"


@dataclass(frozen=True)
class SourceFamilyMasterRecord:
    """Runtime-passive source-family master record contract."""

    source_family: SourceFamily
    source_family_master_id: str
    source_year: int
    source_version: str
    source_release: str | None
    source_document_id: str
    ingestion_run_id: str | None
    run_id: str | None
    master_external_key: str
    status: str
    artifact_reference: str | None
    artifact_checksum_sha256: str | None
    archive_reference: str | None
    archive_checksum_sha256: str | None
    effective_from: str | None
    effective_to: str | None
    record_checksum_sha256: str
    metadata: dict[str, object]
    created_at: str
    updated_at: str

    @property
    def lifecycle_status(self) -> str:
        """Backward-compatible alias for the persisted master status."""

        return self.status


@dataclass(frozen=True)
class SourceFamilyDetailRecord:
    """Runtime-passive source-family detail record contract."""

    source_family: SourceFamily
    source_family_detail_id: str
    source_family_master_id: str
    detail_external_key: str
    source_row_number: int | None
    factor_id: str | None
    factor_name: str | None
    factor_value: str
    factor_unit: str
    status: str
    record_checksum_sha256: str
    raw_fields: dict[str, object]
    normalized_fields: dict[str, object]
    created_at: str
    updated_at: str

    @property
    def lifecycle_status(self) -> str:
        """Backward-compatible alias for the persisted detail status."""

        return self.status


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
    skipped_master_count: int = 0
    skipped_detail_count: int = 0
    validation_failure_count: int = 0
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
        validation_failure_count=len(validation_issues),
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
        "source_version",
        "source_document_id",
        "master_external_key",
        "status",
        "record_checksum_sha256",
        "created_at",
        "updated_at",
    ):
        _append_required_string_issue(
            issues,
            getattr(record, field_name),
            f"master_records[{index}].{field_name}",
        )
    if not isinstance(record.source_year, int) or isinstance(record.source_year, bool):
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_INVALID_SOURCE_YEAR",
                message="source_year must be an integer.",
                field_name=f"master_records[{index}].source_year",
            ),
        )
    if not isinstance(record.metadata, dict):
        issues.append(
            SourceFamilyRepositoryIssue(
                code="SOURCE_FAMILY_REPOSITORY_INVALID_METADATA",
                message="metadata must be a dictionary.",
                field_name=f"master_records[{index}].metadata",
            ),
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
        "status",
        "record_checksum_sha256",
        "created_at",
        "updated_at",
    ):
        _append_required_string_issue(
            issues,
            getattr(record, field_name),
            f"detail_records[{index}].{field_name}",
        )
    for field_name in ("raw_fields", "normalized_fields"):
        if not isinstance(getattr(record, field_name), dict):
            issues.append(
                SourceFamilyRepositoryIssue(
                    code="SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_FIELDS",
                    message="detail field payloads must be dictionaries.",
                    field_name=f"detail_records[{index}].{field_name}",
                ),
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
