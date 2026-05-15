from __future__ import annotations

import importlib
import re
import sys
from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    get_postgresql_phase1_schema_catalog,
    get_required_table_names,
    get_source_family_table_names,
)

EXPECTED_SHARED_TABLE_NAMES = (
    "ingestion_runs",
    "source_documents",
    "parser_runs",
    "schema_bootstrap_states",
    "source_family_year_states",
)

EXPECTED_SOURCE_FAMILY_TABLE_NAMES = {
    SourceFamily.GHG: (
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
    ),
    SourceFamily.DEFRA: (
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
    ),
    SourceFamily.IPCC: (
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    ),
}

EXPECTED_PHASE1_TABLE_NAMES = EXPECTED_SHARED_TABLE_NAMES + tuple(
    table_name
    for table_names in EXPECTED_SOURCE_FAMILY_TABLE_NAMES.values()
    for table_name in table_names
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
)


def _fresh_import_catalog_module():
    sys.modules.pop("carbonfactor_parser.persistence.postgresql_schema_catalog", None)
    return importlib.import_module(
        "carbonfactor_parser.persistence.postgresql_schema_catalog"
    )


def test_catalog_import_is_runtime_passive() -> None:
    _fresh_import_catalog_module()


def test_catalog_import_does_not_read_files_or_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("schema catalog import attempted file open side effects")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("schema catalog import attempted environment reads")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    module = _fresh_import_catalog_module()

    assert hasattr(module, "get_postgresql_phase1_schema_catalog")
    assert open_calls == []
    assert getenv_calls == []


def test_catalog_import_does_not_import_banned_runtime_modules() -> None:
    imported_modules_before = set(sys.modules)

    _fresh_import_catalog_module()

    newly_imported = set(sys.modules) - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )


def test_required_tables_exist() -> None:
    required = get_required_table_names()
    assert set(required) == set(EXPECTED_PHASE1_TABLE_NAMES)
    assert len(required) == len(EXPECTED_PHASE1_TABLE_NAMES)


def test_catalog_contains_exact_phase1_table_contract() -> None:
    catalog = get_postgresql_phase1_schema_catalog()
    table_names = tuple(table.name for table in catalog.tables)

    assert table_names == EXPECTED_PHASE1_TABLE_NAMES
    assert len(table_names) == len(set(table_names))


def test_source_families_have_master_and_detail_tables() -> None:
    catalog = get_postgresql_phase1_schema_catalog()

    assert set(catalog.source_family_tables) == set(SourceFamily)
    for family, expected_table_names in EXPECTED_SOURCE_FAMILY_TABLE_NAMES.items():
        table_names = get_source_family_table_names(family)
        assert table_names == expected_table_names
        assert get_source_family_table_names(family.value) == expected_table_names
        assert len(table_names) == 2
        assert table_names[0].endswith("_masters")
        assert table_names[1].endswith("_details")
        assert table_names[0].startswith(f"{family.value}_")
        assert table_names[1].startswith(f"{family.value}_")


def test_shared_system_tables_are_not_source_family_tables() -> None:
    catalog = get_postgresql_phase1_schema_catalog()
    source_family_table_names = {
        table_name
        for table_names in catalog.source_family_tables.values()
        for table_name in table_names
    }

    assert set(EXPECTED_SHARED_TABLE_NAMES).issubset(
        table.name for table in catalog.tables
    )
    assert set(EXPECTED_SHARED_TABLE_NAMES).isdisjoint(source_family_table_names)


def test_table_names_follow_lowercase_snake_case_and_no_forbidden_fragments() -> None:
    forbidden = ("temp", "test", "fake", "sample", "manual", "json_input")
    snake_case = re.compile(r"^[a-z][a-z0-9_]*$")

    for table_name in get_required_table_names():
        assert snake_case.match(table_name)
        assert not any(fragment in table_name for fragment in forbidden)


def test_detail_tables_reference_master_tables() -> None:
    catalog = get_postgresql_phase1_schema_catalog()

    for family in SourceFamily:
        master_name, detail_name = get_source_family_table_names(family)
        master_table = catalog.get_table(master_name)
        detail_table = catalog.get_table(detail_name)
        master_id = f"{family.value}_emission_factor_master_id"
        master_column_names = tuple(column.name for column in master_table.columns)
        detail_column_names = tuple(column.name for column in detail_table.columns)
        matching_foreign_keys = tuple(
            fk
            for fk in detail_table.foreign_keys
            if fk.column_name == master_id
            and fk.referenced_table_name == master_name
            and fk.referenced_column_name == master_id
        )
        matching_indexes = tuple(
            index
            for index in detail_table.indexes
            if index.column_names == (master_id,)
        )

        assert master_id in master_column_names
        assert master_id in detail_column_names
        assert len(matching_foreign_keys) == 1
        assert len(matching_indexes) == 1


def test_helpers_are_deterministic_and_stable() -> None:
    first_required = get_required_table_names()
    second_required = get_required_table_names()
    assert first_required == second_required
    assert first_required == tuple(sorted(first_required))
    assert first_required == tuple(sorted(EXPECTED_PHASE1_TABLE_NAMES))

    for family in SourceFamily:
        first_family = get_source_family_table_names(family)
        second_family = get_source_family_table_names(family.value)
        assert first_family == second_family


def test_catalog_definitions_are_immutable() -> None:
    catalog = get_postgresql_phase1_schema_catalog()
    with pytest.raises(FrozenInstanceError):
        catalog.tables[0].name = "changed_name"  # type: ignore[misc]
