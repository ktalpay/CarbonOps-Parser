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
from carbonfactor_parser.persistence.repository import (
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    create_persistence_result,
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
    "PersistenceIssue",
    "PersistenceIssueSeverity",
    "PersistenceRepository",
    "PersistenceResult",
    "PersistenceResultStatus",
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceSchema",
    "build_persistence_input_from_normalization_result",
    "create_persistence_result",
    "get_normalized_record_postgresql_schema",
    "render_postgresql_ddl_preview",
)
