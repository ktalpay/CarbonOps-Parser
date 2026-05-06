"""PostgreSQL repository skeleton without runtime database behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from carbonfactor_parser.persistence.input import PersistenceInput
from carbonfactor_parser.persistence.postgresql_options import (
    PostgreSQLPersistenceOptions,
)
from carbonfactor_parser.persistence.repository import (
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceResult,
    PersistenceResultStatus,
    create_persistence_result,
)


@dataclass(frozen=True)
class PostgreSQLPersistenceRepository:
    """Skeleton repository that satisfies the persistence protocol."""

    options: PostgreSQLPersistenceOptions | None = None
    repository_metadata: Mapping[str, object] | None = None

    @property
    def provider_name(self) -> str:
        """Return the deterministic provider identity for this skeleton."""

        return "postgresql"

    def persist(self, persistence_input: PersistenceInput) -> PersistenceResult:
        """Return unsupported; runtime PostgreSQL persistence is deferred."""

        return create_persistence_result(
            status=PersistenceResultStatus.UNSUPPORTED,
            attempted_record_count=len(persistence_input.records),
            persisted_record_count=0,
            issues=(
                PersistenceIssue(
                    code="POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED",
                    message=(
                        "PostgreSQLPersistenceRepository is a skeleton and "
                        "does not connect to PostgreSQL or write records."
                    ),
                    severity=PersistenceIssueSeverity.ERROR,
                ),
            ),
            repository_metadata={
                "provider_name": self.provider_name,
                "skeleton": True,
                "options_provided": self.options is not None,
                "database_connection": False,
                "runtime_write": False,
                "migration_runtime": False,
                **(
                    dict(self.repository_metadata)
                    if self.repository_metadata is not None
                    else {}
                ),
            },
        )
