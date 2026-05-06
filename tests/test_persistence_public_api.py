import carbonfactor_parser.persistence as persistence
from carbonfactor_parser.persistence import input, schema
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceSchema,
    build_persistence_input_from_normalization_result,
    get_normalized_record_postgresql_schema,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "PersistenceInput",
    "PersistenceInputBuildResult",
    "PersistenceInputBuildStatus",
    "PersistenceInputIssue",
    "PersistenceInputRecord",
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceSchema",
    "build_persistence_input_from_normalization_result",
    "get_normalized_record_postgresql_schema",
)

EXPECTED_PUBLIC_EXPORTS = {
    "PersistenceInput": input.PersistenceInput,
    "PersistenceInputBuildResult": input.PersistenceInputBuildResult,
    "PersistenceInputBuildStatus": input.PersistenceInputBuildStatus,
    "PersistenceInputIssue": input.PersistenceInputIssue,
    "PersistenceInputRecord": input.PersistenceInputRecord,
    "PostgreSQLPersistenceColumn": schema.PostgreSQLPersistenceColumn,
    "PostgreSQLPersistenceSchema": schema.PostgreSQLPersistenceSchema,
    "build_persistence_input_from_normalization_result": (
        input.build_persistence_input_from_normalization_result
    ),
    "get_normalized_record_postgresql_schema": (
        schema.get_normalized_record_postgresql_schema
    ),
}


def test_expected_persistence_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "PersistenceInput": PersistenceInput,
        "PersistenceInputBuildResult": PersistenceInputBuildResult,
        "PersistenceInputBuildStatus": PersistenceInputBuildStatus,
        "PersistenceInputIssue": PersistenceInputIssue,
        "PersistenceInputRecord": PersistenceInputRecord,
        "PostgreSQLPersistenceColumn": PostgreSQLPersistenceColumn,
        "PostgreSQLPersistenceSchema": PostgreSQLPersistenceSchema,
        "build_persistence_input_from_normalization_result": (
            build_persistence_input_from_normalization_result
        ),
        "get_normalized_record_postgresql_schema": (
            get_normalized_record_postgresql_schema
        ),
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(persistence, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_persistence_all_lists_expected_public_symbols() -> None:
    assert persistence.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_persistence_public_exports_match_origin_modules() -> None:
    assert {
        name: getattr(persistence, name) for name in EXPECTED_PUBLIC_SYMBOLS
    } == EXPECTED_PUBLIC_EXPORTS


def test_persistence_all_names_resolve_to_package_attributes() -> None:
    for name in persistence.__all__:
        assert hasattr(persistence, name)


def test_persistence_all_excludes_internal_module_names() -> None:
    assert "input" not in persistence.__all__
    assert "schema" not in persistence.__all__
    assert all(not name.startswith("_") for name in persistence.__all__)
