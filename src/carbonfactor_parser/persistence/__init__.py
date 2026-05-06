"""Intentional public exports for persistence boundary contracts."""

from carbonfactor_parser.persistence.ddl_preview import render_postgresql_ddl_preview
from carbonfactor_parser.persistence.input import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    build_persistence_input_from_normalization_result,
)
from carbonfactor_parser.persistence.integration_test_boundary import (
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
    PostgreSQLIntegrationTestBoundary,
    create_postgresql_integration_test_boundary,
    should_skip_postgresql_integration_tests,
)
from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertBuildIssue,
    PostgreSQLInsertBuildResult,
    PostgreSQLInsertBuildStatus,
    PostgreSQLInsertStatement,
    build_postgresql_insert_statement,
)
from carbonfactor_parser.persistence.postgresql_persistence_preview import (
    PostgreSQLPersistencePreview,
    PostgreSQLPersistencePreviewIssue,
    PostgreSQLPersistencePreviewResult,
    PostgreSQLPersistencePreviewStatus,
    build_postgresql_persistence_preview,
)
from carbonfactor_parser.persistence.repository import (
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    create_persistence_result,
)
from carbonfactor_parser.persistence.postgresql_repository import (
    PostgreSQLPersistenceRepository,
)
from carbonfactor_parser.persistence.postgresql_options import (
    PostgreSQLPersistenceOptions,
    PostgreSQLPersistenceOptionsValidationIssue,
    PostgreSQLPersistenceOptionsValidationResult,
    create_postgresql_persistence_options,
    validate_postgresql_persistence_options,
)
from carbonfactor_parser.persistence.schema import (
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceSchema,
    get_normalized_record_postgresql_schema,
)

__all__ = (
    "PersistenceInput",
    "PersistenceInputBuildResult",
    "PersistenceInputBuildStatus",
    "PersistenceInputIssue",
    "PersistenceInputRecord",
    "POSTGRESQL_INTEGRATION_TEST_MARKER",
    "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON",
    "PersistenceIssue",
    "PersistenceIssueSeverity",
    "PersistenceRepository",
    "PersistenceResult",
    "PersistenceResultStatus",
    "PostgreSQLIntegrationTestBoundary",
    "PostgreSQLInsertBuildIssue",
    "PostgreSQLInsertBuildResult",
    "PostgreSQLInsertBuildStatus",
    "PostgreSQLInsertStatement",
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceOptions",
    "PostgreSQLPersistenceOptionsValidationIssue",
    "PostgreSQLPersistenceOptionsValidationResult",
    "PostgreSQLPersistencePreview",
    "PostgreSQLPersistencePreviewIssue",
    "PostgreSQLPersistencePreviewResult",
    "PostgreSQLPersistencePreviewStatus",
    "PostgreSQLPersistenceRepository",
    "PostgreSQLPersistenceSchema",
    "build_persistence_input_from_normalization_result",
    "build_postgresql_insert_statement",
    "build_postgresql_persistence_preview",
    "create_persistence_result",
    "create_postgresql_integration_test_boundary",
    "create_postgresql_persistence_options",
    "get_normalized_record_postgresql_schema",
    "render_postgresql_ddl_preview",
    "should_skip_postgresql_integration_tests",
    "validate_postgresql_persistence_options",
)
