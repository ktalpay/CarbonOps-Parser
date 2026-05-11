"""Tests for source document repository contract metadata helpers."""

from __future__ import annotations

import inspect

from carbonfactor_parser.persistence.source_document_mapping import (
    create_source_document_persistence_mapping,
)
from carbonfactor_parser.persistence.source_document_repository import (
    SourceDocumentRepository,
    SourceDocumentRepositoryIssue,
    SourceDocumentRepositoryPersistStatus,
    create_source_document_repository_persist_result,
    validate_source_document_repository_inputs,
)
from carbonfactor_parser.persistence import (
    source_document_repository as source_document_repository_module,
)


class _InMemorySourceDocumentRepository:
    @property
    def provider_name(self) -> str:
        return "in_memory"

    def persist_source_documents(self, records):
        return create_source_document_repository_persist_result(
            provider_name=self.provider_name,
            records=records,
        )


def _sample_records():
    return create_source_document_persistence_mapping().records


def test_source_document_repository_protocol_shape() -> None:
    repository: SourceDocumentRepository = _InMemorySourceDocumentRepository()

    result = repository.persist_source_documents(_sample_records())

    assert isinstance(repository, SourceDocumentRepository)
    assert repository.provider_name == "in_memory"
    assert result.status is SourceDocumentRepositoryPersistStatus.DECLARED
    assert result.persisted_count == 3
    assert result.issues == ()


def test_source_document_repository_validation_requires_provider_name() -> None:
    validation = validate_source_document_repository_inputs(
        provider_name="",
        records=_sample_records(),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == (
        "SOURCE_DOCUMENT_REPOSITORY_MISSING_PROVIDER_NAME"
    )
    assert validation.issues[0].field_name == "provider_name"


def test_source_document_repository_validation_requires_record_instances() -> None:
    validation = validate_source_document_repository_inputs(
        provider_name="in_memory",
        records=(object(),),
    )

    assert validation.is_valid is False
    assert validation.issues[0].code == "SOURCE_DOCUMENT_REPOSITORY_INVALID_RECORD"
    assert validation.issues[0].field_name == "records[0]"


def test_source_document_repository_persist_result_reports_validation_failure() -> None:
    result = create_source_document_repository_persist_result(
        provider_name="",
        records=(object(),),
    )

    assert result.status is SourceDocumentRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_count == 0
    assert len(result.issues) == 2


def test_source_document_repository_persist_result_snapshots_issues() -> None:
    issues = [
        SourceDocumentRepositoryIssue(
            code="CUSTOM_SOURCE_DOCUMENT_REPOSITORY_WARNING",
            message="custom issue",
            field_name="records",
            severity="warning",
        ),
    ]

    result = create_source_document_repository_persist_result(
        provider_name="in_memory",
        records=_sample_records(),
        issues=issues,
    )
    issues.clear()

    assert result.status is SourceDocumentRepositoryPersistStatus.FAILED_VALIDATION
    assert result.persisted_count == 0
    assert len(result.issues) == 1
    assert result.issues[0].code == "CUSTOM_SOURCE_DOCUMENT_REPOSITORY_WARNING"


def test_source_document_repository_contract_remains_runtime_passive() -> None:
    module_source = inspect.getsource(source_document_repository_module)

    blocked_terms = (
        "connect(",
        "execute(",
        "open(",
        "CREATE TABLE",
        "INSERT INTO",
        "postgres",
        "requests",
        "httpx",
        "urlopen",
    )

    for term in blocked_terms:
        assert term not in module_source
