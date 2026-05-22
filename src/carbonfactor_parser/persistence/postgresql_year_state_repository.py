"""PostgreSQL repository for source-family ingestion year state."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from carbonfactor_parser.persistence.postgresql_runtime_config import (
    POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    coerce_source_family,
    source_family_postgresql_value,
)


SOURCE_FAMILY_YEAR_STATE_TABLE_NAME = "source_family_year_states"


@dataclass(frozen=True)
class SourceFamilyYearState:
    """Latest and next target year for a source family."""

    source_family: SourceFamily
    latest_year: int | None
    next_year: int
    initial_year: int


class PostgreSQLSourceFamilyYearStateRepository:
    """Runtime PostgreSQL year-state repository using a caller connection."""

    def __init__(
        self,
        connection: object,
        *,
        initial_year: int = POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
    ) -> None:
        if initial_year < 1:
            raise ValueError("initial_year must be positive.")
        self._connection = connection
        self._initial_year = initial_year

    @property
    def provider_name(self) -> str:
        """Return the repository provider name."""

        return "postgresql"

    @property
    def initial_year(self) -> int:
        """Return the configured initial target year."""

        return self._initial_year

    def latest_ingested_year(self, source_family: SourceFamily | str) -> int | None:
        """Return the latest ingested year for a source family, if present."""

        family = coerce_source_family(source_family)
        cursor = _execute(
            self._connection,
            """
            SELECT MAX(ingested_year)
            FROM source_family_year_states
            WHERE source_family = %s
            """,
            (source_family_postgresql_value(family),),
        )
        row = _fetchone(cursor)
        if row is not None and row[0] is not None:
            return int(row[0])
        if source_family_postgresql_value(family) != family.value:
            legacy_cursor = _execute(
                self._connection,
                """
                SELECT MAX(ingested_year)
                FROM source_family_year_states
                WHERE source_family = %s
                """,
                (family.value,),
            )
            legacy_row = _fetchone(legacy_cursor)
            if legacy_row is not None and legacy_row[0] is not None:
                return int(legacy_row[0])
        return None

    def next_target_year(self, source_family: SourceFamily | str) -> int:
        """Return initial year for no data or latest ingested year plus one."""

        latest_year = self.latest_ingested_year(source_family)
        if latest_year is None:
            return self._initial_year
        return latest_year + 1

    def get_year_state(
        self,
        source_family: SourceFamily | str,
    ) -> SourceFamilyYearState:
        """Return latest and next target year for a source family."""

        family = coerce_source_family(source_family)
        latest_year = self.latest_ingested_year(family)
        return SourceFamilyYearState(
            source_family=family,
            latest_year=latest_year,
            next_year=self._initial_year if latest_year is None else latest_year + 1,
            initial_year=self._initial_year,
        )

    def record_ingested_year(
        self,
        source_family: SourceFamily | str,
        ingested_year: int,
    ) -> None:
        """Record a completed ingested year idempotently."""

        if ingested_year < 1:
            raise ValueError("ingested_year must be positive.")
        family = coerce_source_family(source_family)
        _execute(
            self._connection,
            """
            INSERT INTO source_family_year_states (
                source_family_year_state_id,
                source_family,
                ingested_year,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, NOW(), NOW())
            ON CONFLICT (source_family, ingested_year)
            DO UPDATE SET updated_at = EXCLUDED.updated_at
            """,
            (str(uuid.uuid4()), source_family_postgresql_value(family), ingested_year),
        )
        _commit(self._connection)


def _execute(
    connection: object,
    statement: str,
    parameters: object | None = None,
) -> object:
    execute = getattr(connection, "execute")
    if parameters is None:
        return execute(statement)
    return execute(statement, parameters)


def _fetchone(cursor: object) -> object | None:
    fetchone = getattr(cursor, "fetchone")
    return fetchone()


def _commit(connection: object) -> None:
    commit = getattr(connection, "commit", None)
    if commit is not None:
        commit()
