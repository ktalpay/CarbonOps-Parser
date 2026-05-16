from __future__ import annotations

import os
import uuid

import pytest

from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.postgresql_runtime_config import (
    POSTGRESQL_RUNTIME_DATABASE_ENV_VAR,
    POSTGRESQL_RUNTIME_DSN_ENV_VAR,
    POSTGRESQL_RUNTIME_HOST_ENV_VAR,
    POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR,
    POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR,
    POSTGRESQL_RUNTIME_USERNAME_ENV_VAR,
    PostgreSQLRuntimeConfigStatus,
    load_postgresql_runtime_config,
    load_postgresql_runtime_config_from_environment,
)
from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupBlockedError,
    start_postgresql_runtime,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    get_required_table_names,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
    SourceFamilyYearState,
)


class FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self._rows = rows

    def fetchone(self) -> tuple[object, ...] | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._rows


class FakeConnection:
    def __init__(
        self,
        *,
        latest_years: dict[str, int | None] | None = None,
        present_tables: tuple[str, ...] = (),
    ) -> None:
        self.latest_years = latest_years or {}
        self.present_tables = set(present_tables)
        self.statements: list[tuple[str, object | None]] = []
        self.commit_count = 0

    def execute(
        self,
        statement: str,
        parameters: object | None = None,
    ) -> FakeCursor:
        self.statements.append((statement, parameters))
        normalized = " ".join(statement.split()).lower()

        if "from source_family_year_states" in normalized and "max" in normalized:
            family = parameters[0]  # type: ignore[index]
            return FakeCursor([(self.latest_years.get(str(family)),)])

        if "from information_schema.tables" in normalized:
            return FakeCursor(
                [(table_name,) for table_name in sorted(self.present_tables)],
            )

        if normalized.startswith("create table if not exists"):
            table_name = normalized.split("create table if not exists ", maxsplit=1)[1]
            table_name = table_name.split(" ", maxsplit=1)[0]
            self.present_tables.add(table_name)

        if normalized.startswith("insert into source_family_year_states"):
            family = parameters[1]  # type: ignore[index]
            year = parameters[2]  # type: ignore[index]
            current = self.latest_years.get(str(family))
            self.latest_years[str(family)] = max(
                int(year),
                int(current) if current is not None else int(year),
            )

        return FakeCursor([])

    def commit(self) -> None:
        self.commit_count += 1


def test_runtime_config_fails_closed_when_required_db_config_is_missing() -> None:
    result = load_postgresql_runtime_config({})

    assert result.status is PostgreSQLRuntimeConfigStatus.BLOCKED
    assert result.config is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST",
        "POSTGRESQL_RUNTIME_CONFIG_MISSING_DATABASE",
        "POSTGRESQL_RUNTIME_CONFIG_MISSING_USERNAME",
        "POSTGRESQL_RUNTIME_CONFIG_MISSING_PASSWORD",
    ]


def test_runtime_startup_fails_closed_when_config_is_blocked() -> None:
    result = load_postgresql_runtime_config({})

    with pytest.raises(PostgreSQLRuntimeStartupBlockedError) as raised:
        start_postgresql_runtime(result)

    assert "POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST" in str(raised.value)


def test_runtime_config_accepts_explicit_dsn_without_exposing_value() -> None:
    private_dsn = "postgresql://user:secret@example.invalid:5432/carbonops"
    result = load_postgresql_runtime_config(
        {
            POSTGRESQL_RUNTIME_DSN_ENV_VAR: private_dsn,
            POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR: "2025",
        },
    )

    assert result.status is PostgreSQLRuntimeConfigStatus.READY
    assert result.config is not None
    assert result.config.uses_dsn is True
    assert result.config.initial_year == 2025
    assert private_dsn not in repr(result)


def test_runtime_config_accepts_explicit_field_configuration() -> None:
    result = load_postgresql_runtime_config(
        {
            POSTGRESQL_RUNTIME_HOST_ENV_VAR: "localhost",
            POSTGRESQL_RUNTIME_DATABASE_ENV_VAR: "carbonops",
            POSTGRESQL_RUNTIME_USERNAME_ENV_VAR: "carbonops",
            POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR: "local-only-password",
        },
    )

    assert result.status is PostgreSQLRuntimeConfigStatus.READY
    assert result.config is not None
    assert result.config.host == "localhost"
    assert result.config.port == 5432
    assert result.config.initial_year == 2024
    assert result.config.password_configured is True
    assert "local-only-password" not in repr(result)


def test_runtime_config_can_read_environment_mapping_when_called() -> None:
    result = load_postgresql_runtime_config_from_environment(
        {
            POSTGRESQL_RUNTIME_DSN_ENV_VAR: "postgresql://example.invalid/db",
        },
    )

    assert result.status is PostgreSQLRuntimeConfigStatus.READY
    assert result.loaded_from_environment is True
    assert result.loaded_from_explicit_values is False


def test_year_state_returns_initial_year_when_no_data_exists() -> None:
    repository = PostgreSQLSourceFamilyYearStateRepository(FakeConnection())

    assert repository.latest_ingested_year(SourceFamily.GHG) is None
    assert repository.next_target_year(SourceFamily.GHG) == 2024
    assert repository.get_year_state(SourceFamily.GHG) == SourceFamilyYearState(
        source_family=SourceFamily.GHG,
        latest_year=None,
        next_year=2024,
        initial_year=2024,
    )


def test_year_state_returns_latest_and_next_year_for_existing_state() -> None:
    repository = PostgreSQLSourceFamilyYearStateRepository(
        FakeConnection(latest_years={"defra": 2026}),
        initial_year=2023,
    )

    assert repository.latest_ingested_year("defra") == 2026
    assert repository.next_target_year("defra") == 2027
    assert repository.get_year_state("defra") == SourceFamilyYearState(
        source_family=SourceFamily.DEFRA,
        latest_year=2026,
        next_year=2027,
        initial_year=2023,
    )


def test_record_ingested_year_is_idempotent_for_source_family_year() -> None:
    connection = FakeConnection()
    repository = PostgreSQLSourceFamilyYearStateRepository(connection)

    repository.record_ingested_year(SourceFamily.IPCC, 2024)
    repository.record_ingested_year(SourceFamily.IPCC, 2024)

    insert_statements = [
        statement
        for statement, _parameters in connection.statements
        if "INSERT INTO source_family_year_states" in statement
    ]
    assert len(insert_statements) == 2
    assert "ON CONFLICT (source_family, ingested_year)" in insert_statements[0]
    assert repository.next_target_year(SourceFamily.IPCC) == 2025
    assert connection.commit_count == 2


def test_runtime_schema_bootstrap_creates_missing_tables_idempotently() -> None:
    connection = FakeConnection()

    first = bootstrap_postgresql_phase1_schema(connection)
    second = bootstrap_postgresql_phase1_schema(connection)

    assert set(first.required_table_names) == set(get_required_table_names())
    assert "source_family_year_states" in first.required_table_names
    assert first.missing_table_names == ()
    assert set(first.created_table_names) == set(get_required_table_names())
    assert second.missing_table_names == ()
    assert second.created_table_names == ()
    assert connection.commit_count == 2
    assert any(
        "CREATE TABLE IF NOT EXISTS source_family_year_states" in statement
        for statement, _parameters in connection.statements
    )
    assert any(
        "CREATE TABLE IF NOT EXISTS ghg_emission_factor_masters" in statement
        and "source_year integer NOT NULL" in statement
        and "artifact_checksum_sha256 text" in statement
        for statement, _parameters in connection.statements
    )
    assert any(
        "CREATE TABLE IF NOT EXISTS ipcc_emission_factor_details" in statement
        and "raw_fields jsonb NOT NULL" in statement
        for statement, _parameters in connection.statements
    )
    assert any(
        "CREATE INDEX IF NOT EXISTS idx_source_family_year_states_family_year"
        in statement
        for statement, _parameters in connection.statements
    )


@pytest.mark.postgresql_integration
def test_docker_postgresql_schema_bootstrap_and_year_state_integration() -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_ph011_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")

        first = bootstrap_postgresql_phase1_schema(connection)
        second = bootstrap_postgresql_phase1_schema(connection)
        repository = PostgreSQLSourceFamilyYearStateRepository(connection)

        assert first.missing_table_names == ()
        assert second.missing_table_names == ()
        assert repository.next_target_year(SourceFamily.DEFRA) == 2024

        repository.record_ingested_year(SourceFamily.GHG, 2024)
        repository.record_ingested_year(SourceFamily.GHG, 2025)

        assert repository.latest_ingested_year(SourceFamily.GHG) == 2025
        assert repository.next_target_year(SourceFamily.GHG) == 2026
