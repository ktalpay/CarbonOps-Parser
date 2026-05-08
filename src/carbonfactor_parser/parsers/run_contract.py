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


def _parser_runs_column_names() -> tuple[str, ...]:
    catalog = get_postgresql_phase1_schema_catalog()
    return tuple(
        column.name for column in catalog.get_table(PARSER_RUNS_TABLE_NAME).columns
    )
