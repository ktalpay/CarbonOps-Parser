import inspect
from pathlib import Path

from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLPersistenceRepository,
)
from carbonfactor_parser.persistence import ddl_preview
from carbonfactor_parser.persistence import postgresql_connection_session_contract
from carbonfactor_parser.persistence import postgresql_execution_adapter_boundary
from carbonfactor_parser.persistence import postgresql_idempotency_conflict_strategy
from carbonfactor_parser.persistence import postgresql_insert_builder
from carbonfactor_parser.persistence import postgresql_persistence_preview
from carbonfactor_parser.persistence import postgresql_repository
from carbonfactor_parser.persistence import postgresql_transaction_policy
from carbonfactor_parser.persistence import schema
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PURE_PERSISTENCE_MODULES = (
    ddl_preview,
    postgresql_connection_session_contract,
    postgresql_execution_adapter_boundary,
    postgresql_idempotency_conflict_strategy,
    postgresql_insert_builder,
    postgresql_persistence_preview,
    postgresql_repository,
    postgresql_transaction_policy,
    schema,
)


def _pyproject_text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def test_psycopg_dependency_is_declared_in_pyproject() -> None:
    text = _pyproject_text()

    assert '"psycopg>=3,<4"' in text


def test_no_competing_postgresql_driver_dependencies_are_declared() -> None:
    text = _pyproject_text().lower()

    assert "asyncpg" not in text
    assert "sqlalchemy" not in text


def test_pure_persistence_modules_do_not_import_psycopg() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        source = inspect.getsource(module)

        assert "import psycopg" not in source
        assert "from psycopg" not in source


def test_pure_persistence_modules_do_not_import_competing_drivers() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        lower_source = inspect.getsource(module).lower()

        assert "asyncpg" not in lower_source
        assert "sqlalchemy" not in lower_source


def test_pure_persistence_modules_have_no_connection_or_execution_calls() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        source = inspect.getsource(module)

        assert "connect(" not in source
        assert "cursor(" not in source
        assert "execute(" not in source
        assert "commit(" not in source
        assert "rollback(" not in source
        assert "begin(" not in source
        assert "os.environ" not in source
        assert "getenv" not in source


def test_repository_skeleton_remains_unsupported_no_execution() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(
        PersistenceInput(
            source_family="defra_desnz",
            source_id="defra_desnz",
            records=(),
        ),
    )

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["runtime_write"] is False
