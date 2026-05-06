import builtins
import inspect
import sqlite3
import urllib.request
from dataclasses import fields

from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    create_persistence_result,
)
from carbonfactor_parser.persistence import repository as repository_module


class FakePersistenceRepository:
    provider_name = "fake_in_memory"

    def persist(self, persistence_input: PersistenceInput) -> PersistenceResult:
        if not persistence_input.records:
            return create_persistence_result(
                status=PersistenceResultStatus.NO_RECORDS,
                attempted_record_count=0,
                persisted_record_count=0,
                issues=(
                    PersistenceIssue(
                        code="FAKE_PERSISTENCE_NO_RECORDS",
                        message="No records were provided to the fake repository.",
                        severity=PersistenceIssueSeverity.WARNING,
                        field_name="records",
                    ),
                ),
                repository_metadata={"provider_name": self.provider_name},
            )

        return create_persistence_result(
            status=PersistenceResultStatus.SUCCESS,
            attempted_record_count=len(persistence_input.records),
            persisted_record_count=len(persistence_input.records),
            repository_metadata={"provider_name": self.provider_name},
        )


def _persistence_input(records=None) -> PersistenceInput:
    return PersistenceInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=records
        if records is not None
        else (
            PersistenceInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_id="defra_desnz:defra_desnz:record-001",
                record_index=1,
                row_number=2,
                normalized_fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                    ("record_index", 1),
                    ("row_number", 2),
                    ("factor_id", "F1"),
                ),
            ),
        ),
    )


def test_repository_protocol_can_be_satisfied_by_fake_in_memory_repository() -> None:
    repository = FakePersistenceRepository()

    assert isinstance(repository, PersistenceRepository)


def test_valid_persistence_input_can_produce_success_result() -> None:
    repository = FakePersistenceRepository()

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.SUCCESS
    assert result.attempted_record_count == 1
    assert result.persisted_record_count == 1
    assert result.issues == ()
    assert result.repository_metadata == {"provider_name": "fake_in_memory"}


def test_no_records_input_produces_no_records_result() -> None:
    repository = FakePersistenceRepository()

    result = repository.persist(_persistence_input(records=()))

    assert result.status == PersistenceResultStatus.NO_RECORDS
    assert result.attempted_record_count == 0
    assert result.persisted_record_count == 0
    assert result.issues[0].code == "FAKE_PERSISTENCE_NO_RECORDS"


def test_failed_or_not_ready_input_is_not_persisted_by_fake_repository() -> None:
    result = create_persistence_result(
        status=PersistenceResultStatus.FAILED,
        attempted_record_count=1,
        persisted_record_count=0,
        issues=(
            PersistenceIssue(
                code="PERSISTENCE_INPUT_NOT_READY",
                message="Persistence input was not ready.",
                severity=PersistenceIssueSeverity.ERROR,
                field_name="persistence_input",
            ),
        ),
    )

    assert result.status == PersistenceResultStatus.FAILED
    assert result.persisted_record_count == 0
    assert result.issues[0].severity == PersistenceIssueSeverity.ERROR


def test_unsupported_result_can_represent_missing_repository_support() -> None:
    result = create_persistence_result(
        status=PersistenceResultStatus.UNSUPPORTED,
        attempted_record_count=0,
        persisted_record_count=0,
        issues=(
            PersistenceIssue(
                code="PERSISTENCE_REPOSITORY_UNSUPPORTED",
                message="No repository implementation is configured.",
                severity=PersistenceIssueSeverity.ERROR,
            ),
        ),
        repository_metadata={"provider_name": "none"},
    )

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.issues[0].code == "PERSISTENCE_REPOSITORY_UNSUPPORTED"
    assert result.repository_metadata == {"provider_name": "none"}


def test_result_contract_has_no_database_runtime_fields() -> None:
    result_fields = {field.name for field in fields(PersistenceResult)}

    assert "connection_string" not in result_fields
    assert "sql" not in result_fields
    assert "migration" not in result_fields
    assert "database_url" not in result_fields


def test_repository_protocol_module_has_no_db_or_sql_behavior() -> None:
    module_source = inspect.getsource(repository_module)

    assert "connect(" not in module_source
    assert "execute(" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source
    assert "postgres" not in module_source.lower()


def test_fake_repository_has_no_db_file_or_network_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("repository protocol test must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    repository = FakePersistenceRepository()
    result = repository.persist(
        _persistence_input(
            records=(
                PersistenceInputRecord(
                    source_family="defra_desnz",
                    source_id="defra_desnz",
                    record_id="record-001",
                    normalized_fields=(
                        ("artifact_reference", str(missing_artifact)),
                    ),
                ),
            ),
        ),
    )

    assert result.status == PersistenceResultStatus.SUCCESS
    assert not missing_artifact.exists()
