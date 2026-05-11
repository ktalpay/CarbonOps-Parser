"""Tests for source-family master/detail repository contract helpers."""

from __future__ import annotations

import inspect

from carbonfactor_parser.persistence import source_family_repository as module
from carbonfactor_parser.persistence.postgresql_schema_catalog import SourceFamily
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    SourceFamilyRepository,
    SourceFamilyRepositoryIssue,
    SourceFamilyRepositoryPersistStatus,
    create_source_family_repository_persist_result,
    source_family_repository_table_names,
    validate_source_family_repository_inputs,
)


class _InMemorySourceFamilyRepository:
    @property
    def provider_name(self) -> str:
        return "in_memory"

    def persist_source_family_records(self, master_records, detail_records):
        return create_source_family_repository_persist_result(
            provider_name=self.provider_name,
            master_records=master_records,
            detail_records=detail_records,
        )


def _sample_master_record(
    *,
    source_family: SourceFamily = SourceFamily.DEFRA,
    source_family_master_id: str = "defra_master_001",
) -> SourceFamilyMasterRecord:
    return SourceFamilyMasterRecord(
        source_family=source_family,
        source_family_master_id=source_family_master_id,
        source_document_id="source_document_001",
        master_external_key="defra_2025_publication",
        lifecycle_status="declared",
        effective_from=None,
        effective_to=None,
        record_checksum_sha256="checksum_master_001",
        created_at="dry_run_timestamp_unavailable",
        updated_at="dry_run_timestamp_unavailable",
    )


def _sample_detail_record(
    *,
    source_family: SourceFamily = SourceFamily.DEFRA,
    source_family_master_id: str = "defra_master_001",
) -> SourceFamilyDetailRecord:
    return SourceFamilyDetailRecord(
        source_family=source_family,
        source_family_detail_id="defra_detail_001",
        source_family_master_id=source_family_master_id,
        detail_external_key="defra_row_001",
        factor_value="1.25",
        factor_unit="kgco2e",
        lifecycle_status="declared",
        record_checksum_sha256="checksum_detail_001",
        created_at="dry_run_timestamp_unavailable",
        updated_at="dry_run_timestamp_unavailable",
    )


def test_source_family_repository_protocol_shape() -> None:
    repository: SourceFamilyRepository = _InMemorySourceFamilyRepository()

    result = repository.persist_source_family_records(
        (_sample_master_record(),),
        (_sample_detail_record(),),
    )

    assert isinstance(repository, SourceFamilyRepository)
    assert repository.provider_name == "in_memory"
    assert result.status is SourceFamilyRepositoryPersistStatus.DECLARED
    assert result.persisted_master_count == 1
    assert result.persisted_detail_count == 1
    assert result.issues == ()


def test_source_family_repository_validation_requires_provider_name() -> None:
    validation = validate_source_family_repository_inputs(
        provider_name="",
        master_records=(_sample_master_record(),),
        detail_records=(_sample_detail_record(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_FAMILY_REPOSITORY_MISSING_PROVIDER_NAME"
    )
    assert validation.issues[0].field_name == "provider_name"


def test_source_family_repository_validation_requires_record_instances() -> None:
    validation = validate_source_family_repository_inputs(
        provider_name="in_memory",
        master_records=(object(),),
        detail_records=(object(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_FAMILY_REPOSITORY_INVALID_MASTER_RECORD"
    )
    assert validation.issues[1].code == (
        "SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_RECORD"
    )


def test_source_family_repository_validation_rejects_missing_required_fields() -> None:
    validation = validate_source_family_repository_inputs(
        provider_name="in_memory",
        master_records=(
            _sample_master_record(source_family_master_id=""),
        ),
        detail_records=(),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_FAMILY_REPOSITORY_MISSING_REQUIRED_FIELD"
    )
    assert validation.issues[0].field_name == (
        "master_records[0].source_family_master_id"
    )


def test_source_family_repository_validation_requires_detail_master_reference() -> None:
    validation = validate_source_family_repository_inputs(
        provider_name="in_memory",
        master_records=(_sample_master_record(),),
        detail_records=(
            _sample_detail_record(source_family_master_id="missing_master"),
        ),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED"
    )
    assert validation.issues[0].field_name == (
        "detail_records[0].source_family_master_id"
    )


def test_source_family_repository_persist_result_reports_validation_failure() -> None:
    result = create_source_family_repository_persist_result(
        provider_name="",
        master_records=(object(),),
        detail_records=(object(),),
    )

    assert result.status is SourceFamilyRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_master_count == 0
    assert result.persisted_detail_count == 0
    assert len(result.issues) == 3


def test_source_family_repository_persist_result_snapshots_inputs_and_issues() -> None:
    master_records = [_sample_master_record()]
    detail_records = [_sample_detail_record()]
    issues = [
        SourceFamilyRepositoryIssue(
            code="CUSTOM_SOURCE_FAMILY_REPOSITORY_WARNING",
            message="custom issue",
            field_name="master_records",
            severity="warning",
        ),
    ]

    result = create_source_family_repository_persist_result(
        provider_name="in_memory",
        master_records=master_records,
        detail_records=detail_records,
        issues=issues,
    )
    master_records.clear()
    detail_records.clear()
    issues.clear()

    assert result.status is SourceFamilyRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_master_count == 0
    assert result.persisted_detail_count == 0
    assert len(result.issues) == 1
    assert result.issues[0].code == "CUSTOM_SOURCE_FAMILY_REPOSITORY_WARNING"


def test_source_family_repository_exposes_catalog_table_names() -> None:
    assert source_family_repository_table_names(SourceFamily.DEFRA) == (
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
    )


def test_source_family_repository_contract_remains_runtime_passive() -> None:
    module_source = inspect.getsource(module)

    blocked_terms = (
        "connect(",
        "execute(",
        "open(",
        "CREATE TABLE",
        "INSERT INTO",
        "psycopg",
        "sqlalchemy",
        "requests",
        "httpx",
        "urlopen",
    )

    for term in blocked_terms:
        assert term not in module_source
