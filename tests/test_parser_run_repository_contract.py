"""Tests for parser run repository contract metadata helpers."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

import pytest

from carbonfactor_parser.parsers.contract_api import (
    ParserRunRepository,
    ParserRunRepositoryIssue,
    ParserRunRepositoryPersistStatus,
    ParserRunStatus,
    create_parser_run_repository_persist_result,
    create_parser_run_request,
    create_parser_run_result,
    create_phase1_parser_input_artifact,
    validate_parser_run_repository_inputs,
)


class _InMemoryRepository:
    @property
    def provider_name(self) -> str:
        return "in_memory"

    def persist_runs(self, runs):
        return create_parser_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=runs,
        )


def _sample_run_result():
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="artifact://phase1/defra_desnz",
    )
    request = create_parser_run_request(
        source_family="defra_desnz",
        artifacts=(artifact,),
    )
    return create_parser_run_result(
        request=request,
        status=ParserRunStatus.DECLARED,
    )


def test_parser_run_repository_protocol_shape() -> None:
    repository: ParserRunRepository = _InMemoryRepository()

    result = repository.persist_runs((_sample_run_result(),))

    assert isinstance(repository, ParserRunRepository)
    assert repository.provider_name == "in_memory"
    assert result.status is ParserRunRepositoryPersistStatus.DECLARED
    assert result.persisted_count == 1
    assert result.issues == ()


def test_parser_run_repository_validation_requires_provider_name() -> None:
    validation = validate_parser_run_repository_inputs(
        provider_name="",
        runs=(_sample_run_result(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == "PARSER_RUN_REPOSITORY_MISSING_PROVIDER_NAME"


def test_parser_run_repository_validation_requires_run_instances() -> None:
    validation = validate_parser_run_repository_inputs(
        provider_name="in_memory",
        runs=(object(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == "PARSER_RUN_REPOSITORY_INVALID_RUN"


def test_parser_run_repository_persist_result_reports_validation_failure() -> None:
    result = create_parser_run_repository_persist_result(
        provider_name="",
        runs=(object(),),
    )

    assert result.status is ParserRunRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_count == 0
    assert len(result.issues) == 2


def test_parser_run_repository_persist_result_snapshots_issue_collections() -> None:
    issues = [
        ParserRunRepositoryIssue(
            code="CUSTOM_REPOSITORY_WARNING",
            message="custom issue",
            field_name="runs",
            severity="warning",
        ),
    ]

    result = create_parser_run_repository_persist_result(
        provider_name="in_memory",
        runs=(_sample_run_result(),),
        issues=issues,
    )
    issues.clear()

    assert result.status is ParserRunRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_count == 0
    assert len(result.issues) == 1
    assert result.issues[0].code == "CUSTOM_REPOSITORY_WARNING"


def test_parser_run_repository_contract_values_are_immutable() -> None:
    issue = ParserRunRepositoryIssue(
        code="CUSTOM_REPOSITORY_WARNING",
        message="custom issue",
        field_name="runs",
    )

    with pytest.raises(FrozenInstanceError):
        issue.code = "CHANGED"


def test_parser_run_repository_persist_status_values_are_deterministic() -> None:
    assert tuple(status.value for status in ParserRunRepositoryPersistStatus) == (
        "declared",
        "failed_validation",
    )


def test_parser_run_repository_contract_remains_runtime_passive() -> None:
    public_members = {
        name
        for contract_type in (
            ParserRunRepository,
            ParserRunRepositoryIssue,
            ParserRunRepositoryPersistStatus,
        )
        for name, _ in inspect.getmembers(contract_type)
        if not name.startswith("_")
    }
    blocked_terms = (
        "db",
        "sql",
        "postgres",
        "http",
        "open",
        "read_file",
        "write",
        "stat_file",
        "exists",
        "fetch",
        "calculate",
        "factor",
    )

    assert not any(
        term in member.lower()
        for member in public_members
        for term in blocked_terms
    )
    assert "parse" not in public_members
    assert "execute" not in public_members
