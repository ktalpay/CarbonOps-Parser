"""Tests for source acquisition run repository contract metadata helpers."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.contract_api import (
    SourceAcquisitionRunRepository,
    SourceAcquisitionRunRepositoryPersistStatus,
    create_source_acquisition_run_repository_persist_result,
    create_source_acquisition_run_request,
    create_source_acquisition_run_result,
    validate_source_acquisition_run_repository_inputs,
)


class _InMemoryRepository:
    @property
    def provider_name(self) -> str:
        return "in_memory"

    def persist_runs(self, runs):
        return create_source_acquisition_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=runs,
        )


def _sample_run_result():
    request = create_source_acquisition_run_request(source_key="defra_desnz")
    return create_source_acquisition_run_result(request)


def test_source_acquisition_run_repository_protocol_shape() -> None:
    repository: SourceAcquisitionRunRepository = _InMemoryRepository()

    result = repository.persist_runs((_sample_run_result(),))

    assert isinstance(repository, SourceAcquisitionRunRepository)
    assert repository.provider_name == "in_memory"
    assert result.status is SourceAcquisitionRunRepositoryPersistStatus.DECLARED
    assert result.persisted_count == 1
    assert result.issues == ()


def test_source_acquisition_run_repository_validation_requires_provider_name() -> None:
    validation = validate_source_acquisition_run_repository_inputs(
        provider_name="",
        runs=(_sample_run_result(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_ACQUISITION_RUN_REPOSITORY_MISSING_PROVIDER_NAME"
    )


def test_source_acquisition_run_repository_validation_requires_run_instances() -> None:
    validation = validate_source_acquisition_run_repository_inputs(
        provider_name="in_memory",
        runs=(object(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == "SOURCE_ACQUISITION_RUN_REPOSITORY_INVALID_RUN"


def test_source_acquisition_run_repository_persist_result_reports_validation_failure() -> None:
    result = create_source_acquisition_run_repository_persist_result(
        provider_name="",
        runs=(object(),),
    )

    assert result.status is SourceAcquisitionRunRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_count == 0
    assert len(result.issues) == 2
