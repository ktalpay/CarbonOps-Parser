"""Local file to normalized persistence dry-run pipeline boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from carbonfactor_parser.normalization import (
    DefraDesnzNormalizationMappingResult,
    DefraDesnzNormalizationMappingStatus,
    NormalizationInputBuildResult,
    NormalizationInputBuildStatus,
    ParserExecutionNormalizationHandoffResult,
    ParserExecutionNormalizationHandoffStatus,
    build_normalization_input_from_parser_execution_handoff,
    build_parser_execution_normalization_handoff,
    map_defra_desnz_normalization_input,
)
from carbonfactor_parser.parsers import (
    ParserExecutionResult,
    ParserExecutionResultStatus,
    ParserFileContentLoadResult,
    ParserFileContentLoadStatus,
    load_parser_file_content_from_local_path,
    parse_defra_desnz_file_content,
)
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    build_persistence_input_from_normalization_result,
    render_postgresql_ddl_preview,
)


class LocalFilePersistenceDryRunStatus(str, Enum):
    """Status for local file to persistence input dry-run pipeline."""

    SUCCESS = "success"
    FAILED = "failed"
    NO_RECORDS = "no_records"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class LocalFilePersistenceDryRunIssue:
    """Issue captured from one dry-run pipeline stage."""

    code: str
    message: str
    stage: str
    severity: str = "error"


@dataclass(frozen=True)
class LocalFilePersistenceDryRunResult:
    """Structured local dry-run result with stage outputs for troubleshooting."""

    status: LocalFilePersistenceDryRunStatus
    source_family: str
    source_id: str
    local_path: str
    load_result: ParserFileContentLoadResult | None = None
    parser_result: ParserExecutionResult | None = None
    handoff_result: ParserExecutionNormalizationHandoffResult | None = None
    normalization_input_build_result: NormalizationInputBuildResult | None = None
    normalization_mapping_result: DefraDesnzNormalizationMappingResult | None = None
    persistence_input_build_result: PersistenceInputBuildResult | None = None
    persistence_input: PersistenceInput | None = None
    ddl_preview: str | None = None
    ddl_preview_metadata: Mapping[str, object] | None = None
    issues: tuple[LocalFilePersistenceDryRunIssue, ...] = ()

    @property
    def is_success(self) -> bool:
        return self.status == LocalFilePersistenceDryRunStatus.SUCCESS


def run_local_file_normalized_persistence_dry_run(
    *,
    local_path: str | Path,
    source_family: str,
    source_id: str,
    content_type: str | None = None,
    format_hint: str | None = None,
    checksum_sha256: str | None = None,
) -> LocalFilePersistenceDryRunResult:
    """Run the local fixture dry-run without database or network behavior."""

    local_path_text = str(local_path)
    load_result = load_parser_file_content_from_local_path(
        source_family=source_family,
        source_id=source_id,
        local_path=local_path,
        content_type=content_type,
        format_hint=format_hint,
        checksum_sha256=checksum_sha256,
    )
    if load_result.status != ParserFileContentLoadStatus.SUCCESS:
        return LocalFilePersistenceDryRunResult(
            status=_status_from_load_result(load_result),
            source_family=source_family,
            source_id=source_id,
            local_path=local_path_text,
            load_result=load_result,
            issues=_issues_from_load_result(load_result),
        )

    parser_result = parse_defra_desnz_file_content(load_result.content_input)
    handoff_result = build_parser_execution_normalization_handoff(parser_result)
    if parser_result.status != ParserExecutionResultStatus.SUCCESS:
        return LocalFilePersistenceDryRunResult(
            status=_status_from_parser_result(parser_result),
            source_family=source_family,
            source_id=source_id,
            local_path=local_path_text,
            load_result=load_result,
            parser_result=parser_result,
            handoff_result=handoff_result,
            issues=_issues_from_parser_result(parser_result),
        )

    normalization_input_build_result = (
        build_normalization_input_from_parser_execution_handoff(handoff_result)
    )
    if (
        normalization_input_build_result.status
        != NormalizationInputBuildStatus.READY
        or normalization_input_build_result.normalization_input is None
    ):
        return LocalFilePersistenceDryRunResult(
            status=LocalFilePersistenceDryRunStatus.FAILED,
            source_family=source_family,
            source_id=source_id,
            local_path=local_path_text,
            load_result=load_result,
            parser_result=parser_result,
            handoff_result=handoff_result,
            normalization_input_build_result=normalization_input_build_result,
            issues=_issues_from_normalization_input_build_result(
                normalization_input_build_result,
            ),
        )

    normalization_mapping_result = map_defra_desnz_normalization_input(
        normalization_input_build_result.normalization_input,
    )
    if (
        normalization_mapping_result.status
        != DefraDesnzNormalizationMappingStatus.SUCCESS
    ):
        return LocalFilePersistenceDryRunResult(
            status=_status_from_normalization_mapping_result(
                normalization_mapping_result,
            ),
            source_family=source_family,
            source_id=source_id,
            local_path=local_path_text,
            load_result=load_result,
            parser_result=parser_result,
            handoff_result=handoff_result,
            normalization_input_build_result=normalization_input_build_result,
            normalization_mapping_result=normalization_mapping_result,
            issues=_issues_from_normalization_mapping_result(
                normalization_mapping_result,
            ),
        )

    persistence_input_build_result = (
        build_persistence_input_from_normalization_result(
            normalization_mapping_result.normalization_result,
            parser_metadata=parser_result.parser_metadata,
            normalization_metadata={
                "normalization_kind": "minimal_defra_desnz_fixture_mapping",
                "is_real_source_normalization": False,
            },
        )
    )
    if persistence_input_build_result.status != PersistenceInputBuildStatus.READY:
        return LocalFilePersistenceDryRunResult(
            status=_status_from_persistence_input_build_result(
                persistence_input_build_result,
            ),
            source_family=source_family,
            source_id=source_id,
            local_path=local_path_text,
            load_result=load_result,
            parser_result=parser_result,
            handoff_result=handoff_result,
            normalization_input_build_result=normalization_input_build_result,
            normalization_mapping_result=normalization_mapping_result,
            persistence_input_build_result=persistence_input_build_result,
            issues=_issues_from_persistence_input_build_result(
                persistence_input_build_result,
            ),
        )

    ddl_preview = render_postgresql_ddl_preview()
    return LocalFilePersistenceDryRunResult(
        status=LocalFilePersistenceDryRunStatus.SUCCESS,
        source_family=source_family,
        source_id=source_id,
        local_path=local_path_text,
        load_result=load_result,
        parser_result=parser_result,
        handoff_result=handoff_result,
        normalization_input_build_result=normalization_input_build_result,
        normalization_mapping_result=normalization_mapping_result,
        persistence_input_build_result=persistence_input_build_result,
        persistence_input=persistence_input_build_result.persistence_input,
        ddl_preview=ddl_preview,
        ddl_preview_metadata={
            "preview_only": True,
            "sql_execution": False,
            "database_connection": False,
            "migration": False,
        },
    )


def _status_from_load_result(
    load_result: ParserFileContentLoadResult,
) -> LocalFilePersistenceDryRunStatus:
    if load_result.status == ParserFileContentLoadStatus.UNSUPPORTED:
        return LocalFilePersistenceDryRunStatus.UNSUPPORTED
    return LocalFilePersistenceDryRunStatus.FAILED


def _status_from_parser_result(
    parser_result: ParserExecutionResult,
) -> LocalFilePersistenceDryRunStatus:
    if parser_result.status == ParserExecutionResultStatus.NO_RECORDS:
        return LocalFilePersistenceDryRunStatus.NO_RECORDS
    if parser_result.status == ParserExecutionResultStatus.UNSUPPORTED:
        return LocalFilePersistenceDryRunStatus.UNSUPPORTED
    return LocalFilePersistenceDryRunStatus.FAILED


def _status_from_normalization_mapping_result(
    mapping_result: DefraDesnzNormalizationMappingResult,
) -> LocalFilePersistenceDryRunStatus:
    if mapping_result.status == DefraDesnzNormalizationMappingStatus.NO_RECORDS:
        return LocalFilePersistenceDryRunStatus.NO_RECORDS
    return LocalFilePersistenceDryRunStatus.FAILED


def _status_from_persistence_input_build_result(
    build_result: PersistenceInputBuildResult,
) -> LocalFilePersistenceDryRunStatus:
    if build_result.status == PersistenceInputBuildStatus.NO_RECORDS:
        return LocalFilePersistenceDryRunStatus.NO_RECORDS
    return LocalFilePersistenceDryRunStatus.FAILED


def _issues_from_load_result(
    load_result: ParserFileContentLoadResult,
) -> tuple[LocalFilePersistenceDryRunIssue, ...]:
    return tuple(
        LocalFilePersistenceDryRunIssue(
            code=issue.code,
            message=issue.message,
            stage="load",
            severity=issue.severity,
        )
        for issue in load_result.issues
    )


def _issues_from_parser_result(
    parser_result: ParserExecutionResult,
) -> tuple[LocalFilePersistenceDryRunIssue, ...]:
    return tuple(
        LocalFilePersistenceDryRunIssue(
            code=issue.code,
            message=issue.message,
            stage="parse",
            severity=issue.severity.value,
        )
        for issue in parser_result.issues
    )


def _issues_from_normalization_input_build_result(
    build_result: NormalizationInputBuildResult,
) -> tuple[LocalFilePersistenceDryRunIssue, ...]:
    return tuple(
        LocalFilePersistenceDryRunIssue(
            code=issue.code,
            message=issue.message,
            stage="normalization_input",
            severity=issue.severity,
        )
        for issue in build_result.issues
    )


def _issues_from_normalization_mapping_result(
    mapping_result: DefraDesnzNormalizationMappingResult,
) -> tuple[LocalFilePersistenceDryRunIssue, ...]:
    return tuple(
        LocalFilePersistenceDryRunIssue(
            code=issue.code,
            message=issue.message,
            stage="normalization_mapping",
            severity=issue.severity.value,
        )
        for issue in mapping_result.normalization_result.issues
    )


def _issues_from_persistence_input_build_result(
    build_result: PersistenceInputBuildResult,
) -> tuple[LocalFilePersistenceDryRunIssue, ...]:
    return tuple(
        LocalFilePersistenceDryRunIssue(
            code=issue.code,
            message=issue.message,
            stage="persistence_input",
            severity=issue.severity,
        )
        for issue in build_result.issues
    )
