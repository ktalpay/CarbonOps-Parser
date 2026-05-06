import carbonfactor_parser.persistence as persistence
from carbonfactor_parser.persistence import (
    ddl_preview,
    input,
    postgresql_options,
    postgresql_repository,
    repository,
    schema,
)
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceOptions,
    PostgreSQLPersistenceOptionsValidationIssue,
    PostgreSQLPersistenceOptionsValidationResult,
    PostgreSQLPersistenceRepository,
    PostgreSQLPersistenceSchema,
    build_persistence_input_from_normalization_result,
    create_persistence_result,
    create_postgresql_persistence_options,
    get_normalized_record_postgresql_schema,
    render_postgresql_ddl_preview,
    validate_postgresql_persistence_options,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "PersistenceInput",
    "PersistenceInputBuildResult",
    "PersistenceInputBuildStatus",
    "PersistenceInputIssue",
    "PersistenceInputRecord",
    "PersistenceIssue",
    "PersistenceIssueSeverity",
    "PersistenceRepository",
    "PersistenceResult",
    "PersistenceResultStatus",
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceOptions",
    "PostgreSQLPersistenceOptionsValidationIssue",
    "PostgreSQLPersistenceOptionsValidationResult",
    "PostgreSQLPersistenceRepository",
    "PostgreSQLPersistenceSchema",
    "build_persistence_input_from_normalization_result",
    "create_persistence_result",
    "create_postgresql_persistence_options",
    "get_normalized_record_postgresql_schema",
    "render_postgresql_ddl_preview",
    "validate_postgresql_persistence_options",
)

EXPECTED_PUBLIC_EXPORTS = {
    "PersistenceInput": input.PersistenceInput,
    "PersistenceInputBuildResult": input.PersistenceInputBuildResult,
    "PersistenceInputBuildStatus": input.PersistenceInputBuildStatus,
    "PersistenceInputIssue": input.PersistenceInputIssue,
    "PersistenceInputRecord": input.PersistenceInputRecord,
    "PersistenceIssue": repository.PersistenceIssue,
    "PersistenceIssueSeverity": repository.PersistenceIssueSeverity,
    "PersistenceRepository": repository.PersistenceRepository,
    "PersistenceResult": repository.PersistenceResult,
    "PersistenceResultStatus": repository.PersistenceResultStatus,
    "PostgreSQLPersistenceColumn": schema.PostgreSQLPersistenceColumn,
    "PostgreSQLPersistenceOptions": (
        postgresql_options.PostgreSQLPersistenceOptions
    ),
    "PostgreSQLPersistenceOptionsValidationIssue": (
        postgresql_options.PostgreSQLPersistenceOptionsValidationIssue
    ),
    "PostgreSQLPersistenceOptionsValidationResult": (
        postgresql_options.PostgreSQLPersistenceOptionsValidationResult
    ),
    "PostgreSQLPersistenceRepository": (
        postgresql_repository.PostgreSQLPersistenceRepository
    ),
    "PostgreSQLPersistenceSchema": schema.PostgreSQLPersistenceSchema,
    "build_persistence_input_from_normalization_result": (
        input.build_persistence_input_from_normalization_result
    ),
    "create_persistence_result": repository.create_persistence_result,
    "create_postgresql_persistence_options": (
        postgresql_options.create_postgresql_persistence_options
    ),
    "get_normalized_record_postgresql_schema": (
        schema.get_normalized_record_postgresql_schema
    ),
    "render_postgresql_ddl_preview": ddl_preview.render_postgresql_ddl_preview,
    "validate_postgresql_persistence_options": (
        postgresql_options.validate_postgresql_persistence_options
    ),
}


def test_expected_persistence_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "PersistenceInput": PersistenceInput,
        "PersistenceInputBuildResult": PersistenceInputBuildResult,
        "PersistenceInputBuildStatus": PersistenceInputBuildStatus,
        "PersistenceInputIssue": PersistenceInputIssue,
        "PersistenceInputRecord": PersistenceInputRecord,
        "PersistenceIssue": PersistenceIssue,
        "PersistenceIssueSeverity": PersistenceIssueSeverity,
        "PersistenceRepository": PersistenceRepository,
        "PersistenceResult": PersistenceResult,
        "PersistenceResultStatus": PersistenceResultStatus,
        "PostgreSQLPersistenceColumn": PostgreSQLPersistenceColumn,
        "PostgreSQLPersistenceOptions": PostgreSQLPersistenceOptions,
        "PostgreSQLPersistenceOptionsValidationIssue": (
            PostgreSQLPersistenceOptionsValidationIssue
        ),
        "PostgreSQLPersistenceOptionsValidationResult": (
            PostgreSQLPersistenceOptionsValidationResult
        ),
        "PostgreSQLPersistenceRepository": PostgreSQLPersistenceRepository,
        "PostgreSQLPersistenceSchema": PostgreSQLPersistenceSchema,
        "build_persistence_input_from_normalization_result": (
            build_persistence_input_from_normalization_result
        ),
        "create_persistence_result": create_persistence_result,
        "create_postgresql_persistence_options": (
            create_postgresql_persistence_options
        ),
        "get_normalized_record_postgresql_schema": (
            get_normalized_record_postgresql_schema
        ),
        "render_postgresql_ddl_preview": render_postgresql_ddl_preview,
        "validate_postgresql_persistence_options": (
            validate_postgresql_persistence_options
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
    assert "repository" not in persistence.__all__
    assert "schema" not in persistence.__all__
    assert "ddl_preview" not in persistence.__all__
    assert "postgresql_options" not in persistence.__all__
    assert "postgresql_repository" not in persistence.__all__
    assert all(not name.startswith("_") for name in persistence.__all__)
