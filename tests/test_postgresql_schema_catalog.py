from __future__ import annotations

import importlib
import re
from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    get_postgresql_phase1_schema_catalog,
    get_required_table_names,
    get_source_family_table_names,
)


def test_catalog_import_is_runtime_passive() -> None:
    importlib.import_module("carbonfactor_parser.persistence.postgresql_schema_catalog")


@pytest.mark.parametrize("module_name", ("requests", "psycopg", "sqlalchemy", "dotenv"))
def test_catalog_import_does_not_import_banned_runtime_modules(module_name: str) -> None:
    import sys

    sys.modules.pop(module_name, None)
    importlib.import_module("carbonfactor_parser.persistence.postgresql_schema_catalog")
    assert module_name not in sys.modules


def test_required_tables_exist() -> None:
    required = get_required_table_names()
    assert "ingestion_runs" in required
    assert "source_documents" in required
    assert "parser_runs" in required
    assert "schema_bootstrap_states" in required


def test_source_families_have_master_and_detail_tables() -> None:
    assert get_source_family_table_names(SourceFamily.GHG) == (
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
    )
    assert get_source_family_table_names(SourceFamily.DEFRA) == (
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
    )
    assert get_source_family_table_names(SourceFamily.IPCC) == (
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    )


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
        detail_table = catalog.get_table(detail_name)
        master_id = f"{family.value}_emission_factor_master_id"
        assert any(
            fk.column_name == master_id and fk.referenced_table_name == master_name
            for fk in detail_table.foreign_keys
        )


def test_helpers_are_deterministic_and_stable() -> None:
    first_required = get_required_table_names()
    second_required = get_required_table_names()
    assert first_required == second_required
    assert first_required == tuple(sorted(first_required))

    first_family = get_source_family_table_names("ghg")
    second_family = get_source_family_table_names("ghg")
    assert first_family == second_family


def test_catalog_definitions_are_immutable() -> None:
    catalog = get_postgresql_phase1_schema_catalog()
    with pytest.raises(FrozenInstanceError):
        catalog.tables[0].name = "changed_name"  # type: ignore[misc]
