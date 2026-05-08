from __future__ import annotations

import importlib
import sys
from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
    PostgreSQLSchemaBootstrapMode,
    PostgreSQLSchemaBootstrapTableStatus,
    build_postgresql_phase1_schema_bootstrap_report,
    build_postgresql_phase1_schema_bootstrap_request,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_required_table_names,
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "httpx",
    "urllib3",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
)


def _fresh_import_bootstrap_module():
    sys.modules.pop(
        "carbonfactor_parser.persistence.postgresql_schema_bootstrap",
        None,
    )
    return importlib.import_module(
        "carbonfactor_parser.persistence.postgresql_schema_bootstrap"
    )


def test_bootstrap_import_is_runtime_passive() -> None:
    _fresh_import_bootstrap_module()


def test_bootstrap_import_does_not_import_runtime_heavy_modules() -> None:
    imported_modules_before = set(sys.modules)

    _fresh_import_bootstrap_module()

    newly_imported = set(sys.modules) - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )


def test_phase1_bootstrap_request_includes_required_catalog_table_names() -> None:
    request = build_postgresql_phase1_schema_bootstrap_request()

    assert request.mode is PostgreSQLSchemaBootstrapMode.CHECK_ONLY
    assert request.required_table_names == get_required_table_names()
    assert request.required_table_names == tuple(
        sorted(request.required_table_names)
    )
    assert "schema_bootstrap_states" in request.required_table_names


def test_phase1_bootstrap_request_ordering_is_deterministic() -> None:
    first = build_postgresql_phase1_schema_bootstrap_request()
    second = build_postgresql_phase1_schema_bootstrap_request()

    assert first == second
    assert first.required_table_names == second.required_table_names


def test_check_only_report_marks_missing_or_skipped_without_creation() -> None:
    required_table_names = get_required_table_names()
    present_table_names = required_table_names[:2]
    skipped_table_names = required_table_names[2:3]

    report = build_postgresql_phase1_schema_bootstrap_report(
        mode=PostgreSQLSchemaBootstrapMode.CHECK_ONLY,
        present_table_names=present_table_names,
        created_table_names=required_table_names[3:4],
        skipped_table_names=skipped_table_names,
    )

    assert report.mode is PostgreSQLSchemaBootstrapMode.CHECK_ONLY
    assert report.present_table_names == present_table_names
    assert report.skipped_table_names == skipped_table_names
    assert report.created_table_names == ()
    assert report.missing_table_names == required_table_names[3:]
    assert all(
        result.status is not PostgreSQLSchemaBootstrapTableStatus.CREATED
        for result in report.table_results
    )
    assert report.no_execution is True
    assert report.creates_tables_now is False


def test_create_missing_report_can_represent_created_tables_without_db_work() -> None:
    required_table_names = get_required_table_names()
    created_table_names = required_table_names[:2]
    present_table_names = required_table_names[2:4]

    report = build_postgresql_phase1_schema_bootstrap_report(
        mode="create_missing",
        present_table_names=present_table_names,
        created_table_names=created_table_names,
        fail_on_missing=False,
    )

    assert report.mode is PostgreSQLSchemaBootstrapMode.CREATE_MISSING
    assert report.created_table_names == created_table_names
    assert report.present_table_names == present_table_names
    assert report.fail_on_missing is False
    assert report.opens_connection is False
    assert report.runs_sql is False
    assert report.creates_tables_now is False
    assert report.runs_migrations is False


def test_bootstrap_report_declares_no_runtime_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("schema bootstrap attempted file side effects")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("schema bootstrap attempted environment reads")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)

    report = build_postgresql_phase1_schema_bootstrap_report()

    assert report.reads_environment is False
    assert report.writes_files is False
    assert report.performs_network_calls is False
    assert open_calls == []
    assert getenv_calls == []


def test_bootstrap_contract_dataclasses_are_immutable() -> None:
    request = build_postgresql_phase1_schema_bootstrap_request()
    report = build_postgresql_phase1_schema_bootstrap_report()

    with pytest.raises(FrozenInstanceError):
        request.mode = (  # type: ignore[misc]
            PostgreSQLSchemaBootstrapMode.CREATE_MISSING
        )
    with pytest.raises(FrozenInstanceError):
        report.table_results[0].status = (  # type: ignore[misc]
            PostgreSQLSchemaBootstrapTableStatus.PRESENT
        )
