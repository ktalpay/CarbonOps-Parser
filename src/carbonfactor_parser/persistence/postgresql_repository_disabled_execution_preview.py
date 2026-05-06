"""Repository-level PostgreSQL disabled execution preview without SQL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.input import PersistenceInput
from carbonfactor_parser.persistence.postgresql_disabled_runtime_execution_adapter import (
    PostgreSQLDisabledRuntimeExecutionResult,
    build_postgresql_disabled_runtime_execution_result,
)
from carbonfactor_parser.persistence.postgresql_idempotency_conflict_strategy import (
    build_default_postgresql_idempotency_conflict_strategy,
)
from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertBuildIssue,
    PostgreSQLInsertBuildStatus,
    build_postgresql_insert_statement,
)
from carbonfactor_parser.persistence.postgresql_transaction_policy import (
    build_default_postgresql_transaction_policy,
)


class PostgreSQLRepositoryDisabledExecutionPreviewStatus(str, Enum):
    """Status values for repository-level disabled execution previews."""

    DISABLED = "disabled"
    NO_RECORDS = "no_records"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PostgreSQLRepositoryDisabledExecutionPreviewIssue:
    """Issue for repository-level disabled execution preview diagnostics."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLRepositoryDisabledExecutionPreviewResult:
    """Repository-adjacent disabled execution preview result."""

    status: PostgreSQLRepositoryDisabledExecutionPreviewStatus
    reason: str
    no_execution: bool
    source_family: str
    source_id: str
    attempted_record_count: int
    insert_build_status: PostgreSQLInsertBuildStatus | None = None
    disabled_runtime_result: PostgreSQLDisabledRuntimeExecutionResult | None = None
    issues: tuple[PostgreSQLRepositoryDisabledExecutionPreviewIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLRepositoryDisabledExecutionPreviewDescription:
    """Side-effect-free description of the repository preview boundary."""

    accepts_persistence_input: bool
    builds_insert_statement: bool
    builds_disabled_runtime_result: bool
    returns_persistence_result: bool
    opens_connection: bool
    creates_cursor: bool
    runs_sql: bool
    writes_records: bool
    starts_transaction: bool
    commits_transaction: bool
    rolls_back_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    persist_behavior_changed: bool
    notes: tuple[str, ...]


def build_postgresql_repository_disabled_execution_preview(
    persistence_input: PersistenceInput,
) -> PostgreSQLRepositoryDisabledExecutionPreviewResult:
    """Build repository-level disabled execution preview metadata."""

    insert_result = build_postgresql_insert_statement(persistence_input)
    if insert_result.statement is None:
        status = _preview_status_for_insert_build(insert_result.status)
        runtime_result = build_postgresql_disabled_runtime_execution_result()
        return PostgreSQLRepositoryDisabledExecutionPreviewResult(
            status=status,
            reason=_reason_for_insert_build_status(insert_result.status),
            no_execution=True,
            source_family=persistence_input.source_family,
            source_id=persistence_input.source_id,
            attempted_record_count=len(persistence_input.records),
            insert_build_status=insert_result.status,
            disabled_runtime_result=runtime_result,
            issues=tuple(_insert_issues(insert_result.issues)),
        )

    runtime_result = build_postgresql_disabled_runtime_execution_result(
        statement=insert_result.statement,
        transaction_policy=build_default_postgresql_transaction_policy(),
        conflict_strategy=build_default_postgresql_idempotency_conflict_strategy(),
    )

    return PostgreSQLRepositoryDisabledExecutionPreviewResult(
        status=PostgreSQLRepositoryDisabledExecutionPreviewStatus.DISABLED,
        reason=(
            "PostgreSQL repository disabled execution preview was built; "
            "runtime persistence remains unsupported."
        ),
        no_execution=True,
        source_family=persistence_input.source_family,
        source_id=persistence_input.source_id,
        attempted_record_count=len(persistence_input.records),
        insert_build_status=insert_result.status,
        disabled_runtime_result=runtime_result,
        issues=(
            PostgreSQLRepositoryDisabledExecutionPreviewIssue(
                code="POSTGRESQL_REPOSITORY_DISABLED_EXECUTION_PREVIEW",
                message=(
                    "Repository preview is diagnostic metadata only and does "
                    "not persist, write, or run SQL."
                ),
                severity="warning",
            ),
        ),
    )


def describe_postgresql_repository_disabled_execution_preview() -> (
    PostgreSQLRepositoryDisabledExecutionPreviewDescription
):
    """Describe repository disabled execution preview without side effects."""

    return PostgreSQLRepositoryDisabledExecutionPreviewDescription(
        accepts_persistence_input=True,
        builds_insert_statement=True,
        builds_disabled_runtime_result=True,
        returns_persistence_result=False,
        opens_connection=False,
        creates_cursor=False,
        runs_sql=False,
        writes_records=False,
        starts_transaction=False,
        commits_transaction=False,
        rolls_back_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        persist_behavior_changed=False,
        notes=(
            "Repository-level preview diagnostics only.",
            "PostgreSQLPersistenceRepository.persist remains unsupported.",
            "Insert SQL text is preserved only as disabled preview metadata.",
            "No PostgreSQL connection, cursor, transaction, or write occurs.",
        ),
    )


def _preview_status_for_insert_build(
    status: PostgreSQLInsertBuildStatus,
) -> PostgreSQLRepositoryDisabledExecutionPreviewStatus:
    if status == PostgreSQLInsertBuildStatus.NO_RECORDS:
        return PostgreSQLRepositoryDisabledExecutionPreviewStatus.NO_RECORDS
    if status == PostgreSQLInsertBuildStatus.UNSUPPORTED:
        return PostgreSQLRepositoryDisabledExecutionPreviewStatus.UNSUPPORTED
    return PostgreSQLRepositoryDisabledExecutionPreviewStatus.FAILED


def _reason_for_insert_build_status(status: PostgreSQLInsertBuildStatus) -> str:
    if status == PostgreSQLInsertBuildStatus.NO_RECORDS:
        return (
            "PersistenceInput has no records; repository disabled execution "
            "preview remains no-execution."
        )
    return (
        "PostgreSQL insert statement was not ready; repository disabled "
        "execution preview remains no-execution."
    )


def _insert_issues(
    insert_issues: tuple[PostgreSQLInsertBuildIssue, ...],
) -> tuple[PostgreSQLRepositoryDisabledExecutionPreviewIssue, ...]:
    if not insert_issues:
        return (
            PostgreSQLRepositoryDisabledExecutionPreviewIssue(
                code="POSTGRESQL_REPOSITORY_PREVIEW_NO_STATEMENT",
                message=(
                    "No PostgreSQL insert statement was available for the "
                    "repository disabled execution preview."
                ),
                severity="warning",
            ),
        )

    return tuple(
        PostgreSQLRepositoryDisabledExecutionPreviewIssue(
            code=issue.code,
            message=issue.message,
            field_name=issue.field_name,
            severity=issue.severity,
        )
        for issue in insert_issues
    )
