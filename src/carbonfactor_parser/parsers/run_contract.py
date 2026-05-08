"""Runtime-passive parser run/result contract boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_postgresql_phase1_schema_catalog,
)
from carbonfactor_parser.persistence.source_document_mapping import (
    create_source_document_persistence_mapping,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentPersistenceMappingResult,
)


PARSER_RUNS_TABLE_NAME = "parser_runs"
DRY_RUN_TIMESTAMP_LABEL = "dry_run_timestamp_unavailable"
PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)


class ParserRunStatus(str, Enum):
    """Runtime-passive parser run contract status values."""

    NOT_STARTED = "not_started"


@dataclass(frozen=True)
class ParserRunRequest:
    """Dry-run parser request for one mapped source document."""

    parser_run_id: str
    source_document_id: str
    source_family: str
    source_document_uri: str
    source_checksum_sha256: str | None
    parser_status: ParserRunStatus
    error_details: tuple[str, ...]
    created_at: str
    updated_at: str
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class ParserResultSummary:
    """Deterministic parser result summary before parser execution."""

    requested_source_document_count: int
    parsed_record_count: int
    issue_count: int
    warning_count: int
    error_count: int


@dataclass(frozen=True)
class ParserRunContractResult:
    """Runtime-passive parser run/result contract for Phase 1 documents."""

    status: ParserRunStatus
    mode: SourceAcquisitionPlanMode
    table_name: str
    column_names: tuple[str, ...]
    selected_source_families: tuple[str, ...]
    requests: tuple[ParserRunRequest, ...]
    summary: ParserResultSummary


@dataclass(frozen=True)
class ParserRunContractValidationIssue:
    """Validation issue for parser run/result contract metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserRunContractValidationResult:
    """Validation result for parser run/result contract metadata."""

    issues: tuple[ParserRunContractValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_phase1_parser_run_contract(
    mapping: SourceDocumentPersistenceMappingResult | None = None,
) -> ParserRunContractResult:
    """Derive parser run requests without reading files or executing parsers."""

    active_mapping = (
        create_source_document_persistence_mapping() if mapping is None else mapping
    )
    if active_mapping.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run parser run contracts are supported.")

    requests = tuple(
        ParserRunRequest(
            parser_run_id=f"dry_run_parser_run_{index:03d}_{record.source_family}",
            source_document_id=record.source_document_id,
            source_family=record.source_family,
            source_document_uri=record.source_document_uri,
            source_checksum_sha256=record.source_checksum_sha256,
            parser_status=ParserRunStatus.NOT_STARTED,
            error_details=(),
            created_at=DRY_RUN_TIMESTAMP_LABEL,
            updated_at=DRY_RUN_TIMESTAMP_LABEL,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for index, record in enumerate(active_mapping.records, start=1)
    )

    return ParserRunContractResult(
        status=ParserRunStatus.NOT_STARTED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        table_name=PARSER_RUNS_TABLE_NAME,
        column_names=_parser_runs_column_names(),
        selected_source_families=active_mapping.selected_source_families,
        requests=requests,
        summary=ParserResultSummary(
            requested_source_document_count=len(requests),
            parsed_record_count=0,
            issue_count=0,
            warning_count=0,
            error_count=0,
        ),
    )


def validate_parser_run_contract(
    contract: ParserRunContractResult,
) -> ParserRunContractValidationResult:
    """Validate parser run/result metadata without executing parsers."""

    issues: list[ParserRunContractValidationIssue] = []

    if contract.status is not ParserRunStatus.NOT_STARTED:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_INVALID_STATUS",
                message="status must be the dry-run not_started status.",
                field_name="status",
            ),
        )

    if contract.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_INVALID_MODE",
                message="mode must be dry_run.",
                field_name="mode",
            ),
        )

    _validate_source_family_selection(contract, issues)
    _validate_requests(contract.requests, issues)
    _validate_summary(contract, issues)

    return ParserRunContractValidationResult(issues=tuple(issues))


def _parser_runs_column_names() -> tuple[str, ...]:
    catalog = get_postgresql_phase1_schema_catalog()
    return tuple(
        column.name for column in catalog.get_table(PARSER_RUNS_TABLE_NAME).columns
    )


def _validate_source_family_selection(
    contract: ParserRunContractResult,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not contract.selected_source_families:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_MISSING_SOURCE_FAMILIES",
                message="selected_source_families must not be empty.",
                field_name="selected_source_families",
            ),
        )

    for index, source_family in enumerate(contract.selected_source_families):
        if source_family not in PHASE1_SOURCE_FAMILIES:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_UNSUPPORTED_SOURCE_FAMILY",
                    message="selected source family must be supported by Phase 1.",
                    field_name=f"selected_source_families[{index}]",
                ),
            )


def _validate_requests(
    requests: tuple[ParserRunRequest, ...],
    issues: list[ParserRunContractValidationIssue],
) -> None:
    parser_run_ids: set[str] = set()
    source_document_ids: set[str] = set()

    for index, request in enumerate(requests):
        _validate_required_text(
            request.parser_run_id,
            f"requests[{index}].parser_run_id",
            "PARSER_RUN_CONTRACT_MISSING_PARSER_RUN_ID",
            "parser_run_id must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            request.source_document_id,
            f"requests[{index}].source_document_id",
            "PARSER_RUN_CONTRACT_MISSING_SOURCE_DOCUMENT_ID",
            "source_document_id must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            request.source_document_uri,
            f"requests[{index}].source_document_uri",
            "PARSER_RUN_CONTRACT_MISSING_SOURCE_DOCUMENT_URI",
            "source_document_uri must be a non-empty string.",
            issues,
        )

        if request.source_family not in PHASE1_SOURCE_FAMILIES:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_UNSUPPORTED_REQUEST_SOURCE_FAMILY",
                    message="request source family must be supported by Phase 1.",
                    field_name=f"requests[{index}].source_family",
                ),
            )

        if not isinstance(request.parser_status, ParserRunStatus):
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_INVALID_REQUEST_STATUS",
                    message="request parser_status must be a defined parser run status.",
                    field_name=f"requests[{index}].parser_status",
                ),
            )
        elif request.parser_status is not ParserRunStatus.NOT_STARTED:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_UNEXPECTED_REQUEST_STATUS",
                    message="request parser_status must remain not_started.",
                    field_name=f"requests[{index}].parser_status",
                ),
            )

        if request.mode is not SourceAcquisitionPlanMode.DRY_RUN:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_INVALID_REQUEST_MODE",
                    message="request mode must be dry_run.",
                    field_name=f"requests[{index}].mode",
                ),
            )

        if request.parser_run_id in parser_run_ids:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_DUPLICATE_PARSER_RUN_ID",
                    message="parser_run_id values must be unique.",
                    field_name=f"requests[{index}].parser_run_id",
                ),
            )
        parser_run_ids.add(request.parser_run_id)

        if request.source_document_id in source_document_ids:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_DUPLICATE_SOURCE_DOCUMENT_ID",
                    message="source_document_id values must be unique.",
                    field_name=f"requests[{index}].source_document_id",
                ),
            )
        source_document_ids.add(request.source_document_id)


def _validate_summary(
    contract: ParserRunContractResult,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    summary = contract.summary
    for field_name, value in (
        (
            "summary.requested_source_document_count",
            summary.requested_source_document_count,
        ),
        ("summary.parsed_record_count", summary.parsed_record_count),
        ("summary.issue_count", summary.issue_count),
        ("summary.warning_count", summary.warning_count),
        ("summary.error_count", summary.error_count),
    ):
        if value < 0:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_CONTRACT_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative.",
                    field_name=field_name,
                ),
            )

    if summary.requested_source_document_count != len(contract.requests):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_SUMMARY_REQUEST_COUNT_MISMATCH",
                message="requested source document count must match request count.",
                field_name="summary.requested_source_document_count",
            ),
        )

    if summary.warning_count + summary.error_count > summary.issue_count:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_SUMMARY_ISSUE_TOTAL_MISMATCH",
                message="warning and error counts must not exceed issue count.",
                field_name="summary.issue_count",
            ),
        )

    if (
        summary.parsed_record_count != 0
        or summary.issue_count != 0
        or summary.warning_count != 0
        or summary.error_count != 0
    ):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_CONTRACT_DRY_RUN_SUMMARY_NOT_ZERO",
                message="not_started dry-run parser summaries must remain zero-count.",
                field_name="summary",
            ),
        )


def _validate_required_text(
    value: str,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserRunContractValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )
