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

    assert repository.provider_name == "postgresql"


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
        "implementation_state": "skeleton",
    }


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
