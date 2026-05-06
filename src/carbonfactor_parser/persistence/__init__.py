"""Intentional public exports for persistence boundary contracts."""

from carbonfactor_parser.persistence.input import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    build_persistence_input_from_normalization_result,
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
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceSchema",
    "build_persistence_input_from_normalization_result",
    "get_normalized_record_postgresql_schema",
)
