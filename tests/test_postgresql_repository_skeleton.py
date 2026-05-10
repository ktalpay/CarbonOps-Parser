import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_repository as repository_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResultStatus,
    PostgreSQLPersistenceOptions,
    PostgreSQLPersistenceRepository,
    PostgreSQLRepositoryRuntimeSafetyGate,
    PostgreSQLRepositoryRuntimeSafetyGateStatus,
    describe_postgresql_repository_runtime_safety_gate,
    evaluate_postgresql_repository_runtime_safety_gate,
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
            PersistenceInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_id="defra_desnz:defra_desnz:record-002",
                record_index=2,
                row_number=3,
                normalized_fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                    ("record_index", 2),
                    ("row_number", 3),
                    ("factor_id", "F2"),
                ),
            ),
        ),
    )


def test_postgresql_repository_skeleton_imports_from_public_api() -> None:
    repository = PostgreSQLPersistenceRepository()
    description = describe_postgresql_repository_runtime_safety_gate()

    assert repository.provider_name == "postgresql"
    assert description.disabled_by_default is True
    assert description.protects_repository_persist is True
    assert description.opens_connection is False
    assert description.runs_sql is False
    assert description.writes_records is False


def test_postgresql_repository_skeleton_satisfies_protocol() -> None:
    repository: PersistenceRepository = PostgreSQLPersistenceRepository()

    assert isinstance(repository, PersistenceRepository)
    assert repository.provider_name == "postgresql"


def test_constructor_has_no_db_config_credential_or_network_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("constructor must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    repository = PostgreSQLPersistenceRepository(
        repository_metadata={"boundary": "skeleton"},
    )

    assert repository.provider_name == "postgresql"
    assert repository.repository_metadata == {"boundary": "skeleton"}


def test_persist_returns_unsupported_not_implemented_result() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.attempted_record_count == 2
    assert result.persisted_record_count == 0
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED",
    ]
    assert result.issues[0].severity == PersistenceIssueSeverity.ERROR


def test_persist_preserves_attempted_record_count_for_empty_input() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(_persistence_input(records=()))

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.attempted_record_count == 0
    assert result.persisted_record_count == 0


def test_persist_returns_skeleton_metadata_without_runtime_claims() -> None:
    repository = PostgreSQLPersistenceRepository(
        repository_metadata={"implementation_state": "skeleton"},
    )

    result = repository.persist(_persistence_input())

    assert result.repository_metadata == {
        "provider_name": "postgresql",
        "skeleton": True,
        "options_provided": False,
        "database_connection": False,
        "runtime_write": False,
        "migration_runtime": False,
        "repository_runtime_enabled": False,
        "repository_runtime_safety_gate_status": "disabled",
        "repository_runtime_requested": False,
        "repository_runtime_no_execution": True,
        "repository_runtime_persist_behavior_changed": False,
        "implementation_state": "skeleton",
    }


def test_repository_metadata_cannot_override_runtime_safety_flags() -> None:
    repository = PostgreSQLPersistenceRepository(
        repository_metadata={
            "database_connection": True,
            "runtime_write": True,
            "migration_runtime": True,
            "repository_runtime_enabled": True,
            "provider_name": "unsafe",
            "implementation_state": "caller-metadata",
        },
        runtime_safety_gate=PostgreSQLRepositoryRuntimeSafetyGate(
            requested=True,
            allow_repository_runtime_persistence=True,
        ),
    )

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.repository_metadata is not None
    assert result.repository_metadata["provider_name"] == "postgresql"
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["runtime_write"] is False
    assert result.repository_metadata["migration_runtime"] is False
    assert result.repository_metadata["repository_runtime_enabled"] is False
    assert result.repository_metadata["repository_runtime_safety_gate_status"] == (
        "blocked"
    )
    assert result.repository_metadata["repository_runtime_requested"] is True
    assert result.repository_metadata["repository_runtime_no_execution"] is True
    assert result.repository_metadata["implementation_state"] == "caller-metadata"


def test_repository_runtime_safety_gate_blocks_runtime_intent() -> None:
    decision = evaluate_postgresql_repository_runtime_safety_gate(
        PostgreSQLRepositoryRuntimeSafetyGate(
            requested=True,
            allow_repository_runtime_persistence=True,
        ),
    )

    assert decision.status is PostgreSQLRepositoryRuntimeSafetyGateStatus.BLOCKED
    assert decision.requested is True
    assert decision.no_execution is True
    assert decision.repository_runtime_enabled is False
    assert decision.persist_behavior_changed is False
    assert decision.opens_connection is False
    assert decision.runs_sql is False
    assert decision.writes_records is False
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_REPOSITORY_RUNTIME_REQUEST_BLOCKED",
        "POSTGRESQL_REPOSITORY_RUNTIME_ALLOW_FLAG_NOT_SUPPORTED",
    ]


def test_persist_has_no_db_file_or_network_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("repository skeleton must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    repository = PostgreSQLPersistenceRepository()
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

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert not missing_artifact.exists()


def test_repository_skeleton_accepts_options_without_connecting(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("repository skeleton must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    repository = PostgreSQLPersistenceRepository(
        options=PostgreSQLPersistenceOptions(
            host="localhost",
            port=5432,
            database="carbonops_test",
            username="carbonops",
            password_set=True,
        ),
    )

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.repository_metadata["options_provided"] is True


def test_repository_skeleton_has_no_db_dependency_or_runtime_sql_behavior() -> None:
    module_source = inspect.getsource(repository_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "render_postgresql_ddl_preview" not in module_source
    assert "connect(" not in module_source
    assert ".execute" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source
