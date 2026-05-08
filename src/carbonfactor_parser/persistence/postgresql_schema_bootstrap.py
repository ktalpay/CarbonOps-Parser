"""Runtime-passive PostgreSQL schema bootstrap boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_required_table_names,
)


class PostgreSQLSchemaBootstrapMode(str, Enum):
    """Caller intent for future PostgreSQL schema bootstrap handling."""

    CHECK_ONLY = "check_only"
    CREATE_MISSING = "create_missing"


class PostgreSQLSchemaBootstrapTableStatus(str, Enum):
    """Per-table status values for schema bootstrap reports."""

    REQUIRED = "required"
    PRESENT = "present"
    MISSING = "missing"
    CREATED = "created"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapRequest:
    """Schema bootstrap intent metadata without runtime execution."""

    mode: PostgreSQLSchemaBootstrapMode
    required_table_names: tuple[str, ...]
    fail_on_missing: bool = True


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapTableResult:
    """Reported status for one required schema table."""

    table_name: str
    status: PostgreSQLSchemaBootstrapTableStatus
    reason: str = ""


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapReport:
    """Runtime-passive schema bootstrap request report."""

    mode: PostgreSQLSchemaBootstrapMode
    required_table_names: tuple[str, ...]
    table_results: tuple[PostgreSQLSchemaBootstrapTableResult, ...]
    fail_on_missing: bool
    no_execution: bool
    opens_connection: bool
    runs_sql: bool
    creates_tables_now: bool
    runs_migrations: bool
    reads_environment: bool
    writes_files: bool
    performs_network_calls: bool

    @property
    def missing_table_names(self) -> tuple[str, ...]:
        return tuple(
            result.table_name
            for result in self.table_results
            if result.status is PostgreSQLSchemaBootstrapTableStatus.MISSING
        )

    @property
    def created_table_names(self) -> tuple[str, ...]:
        return tuple(
            result.table_name
            for result in self.table_results
            if result.status is PostgreSQLSchemaBootstrapTableStatus.CREATED
        )

    @property
    def present_table_names(self) -> tuple[str, ...]:
        return tuple(
            result.table_name
            for result in self.table_results
            if result.status is PostgreSQLSchemaBootstrapTableStatus.PRESENT
        )

    @property
    def skipped_table_names(self) -> tuple[str, ...]:
        return tuple(
            result.table_name
            for result in self.table_results
            if result.status is PostgreSQLSchemaBootstrapTableStatus.SKIPPED
        )


def build_postgresql_phase1_schema_bootstrap_request(
    mode: PostgreSQLSchemaBootstrapMode | str = (
        PostgreSQLSchemaBootstrapMode.CHECK_ONLY
    ),
    *,
    fail_on_missing: bool = True,
) -> PostgreSQLSchemaBootstrapRequest:
    """Build a deterministic Phase 1 schema bootstrap request."""

    return PostgreSQLSchemaBootstrapRequest(
        mode=PostgreSQLSchemaBootstrapMode(mode),
        required_table_names=get_required_table_names(),
        fail_on_missing=fail_on_missing,
    )


def build_postgresql_phase1_schema_bootstrap_report(
    mode: PostgreSQLSchemaBootstrapMode | str = (
        PostgreSQLSchemaBootstrapMode.CHECK_ONLY
    ),
    *,
    present_table_names: tuple[str, ...] = (),
    created_table_names: tuple[str, ...] = (),
    skipped_table_names: tuple[str, ...] = (),
    fail_on_missing: bool = True,
) -> PostgreSQLSchemaBootstrapReport:
    """Build a passive report for Phase 1 schema bootstrap status metadata."""

    request = build_postgresql_phase1_schema_bootstrap_request(
        mode=mode,
        fail_on_missing=fail_on_missing,
    )
    present_tables = set(present_table_names)
    created_tables = set(created_table_names)
    skipped_tables = set(skipped_table_names)

    table_results = tuple(
        PostgreSQLSchemaBootstrapTableResult(
            table_name=table_name,
            status=_resolve_table_status(
                table_name=table_name,
                mode=request.mode,
                present_table_names=present_tables,
                created_table_names=created_tables,
                skipped_table_names=skipped_tables,
            ),
            reason=_resolve_table_reason(
                table_name=table_name,
                mode=request.mode,
                present_table_names=present_tables,
                created_table_names=created_tables,
                skipped_table_names=skipped_tables,
            ),
        )
        for table_name in request.required_table_names
    )

    return PostgreSQLSchemaBootstrapReport(
        mode=request.mode,
        required_table_names=request.required_table_names,
        table_results=table_results,
        fail_on_missing=request.fail_on_missing,
        no_execution=True,
        opens_connection=False,
        runs_sql=False,
        creates_tables_now=False,
        runs_migrations=False,
        reads_environment=False,
        writes_files=False,
        performs_network_calls=False,
    )


def _resolve_table_status(
    *,
    table_name: str,
    mode: PostgreSQLSchemaBootstrapMode,
    present_table_names: set[str],
    created_table_names: set[str],
    skipped_table_names: set[str],
) -> PostgreSQLSchemaBootstrapTableStatus:
    if table_name in present_table_names:
        return PostgreSQLSchemaBootstrapTableStatus.PRESENT
    if (
        mode is PostgreSQLSchemaBootstrapMode.CREATE_MISSING
        and table_name in created_table_names
    ):
        return PostgreSQLSchemaBootstrapTableStatus.CREATED
    if table_name in skipped_table_names:
        return PostgreSQLSchemaBootstrapTableStatus.SKIPPED
    return PostgreSQLSchemaBootstrapTableStatus.MISSING


def _resolve_table_reason(
    *,
    table_name: str,
    mode: PostgreSQLSchemaBootstrapMode,
    present_table_names: set[str],
    created_table_names: set[str],
    skipped_table_names: set[str],
) -> str:
    if table_name in present_table_names:
        return "Required table was reported present by caller metadata."
    if (
        mode is PostgreSQLSchemaBootstrapMode.CREATE_MISSING
        and table_name in created_table_names
    ):
        return "Required table was reported created by caller metadata."
    if table_name in skipped_table_names:
        return "Required table was reported skipped by caller metadata."
    return "Required table was not reported present or created."
