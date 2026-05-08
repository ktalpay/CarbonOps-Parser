"""Runtime-passive parser execution boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.run_contract import (
    ParserRunContractResult,
    ParserRunRequest,
    ParserRunStatus,
    create_phase1_parser_run_contract,
)
from carbonfactor_parser.parsers.selection_registry_contract import (
    ParserSelection,
    ParserSelectionResult,
    select_phase1_parsers,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode


class ParserExecutionBoundaryStatus(str, Enum):
    """Runtime-passive parser execution boundary status values."""

    PLANNED = "planned"


@dataclass(frozen=True)
class ParserExecutionBoundaryDescriptor:
    """Contract-level parser execution boundary behavior flags."""

    mode: SourceAcquisitionPlanMode
    status: ParserExecutionBoundaryStatus
    instantiates_parsers: bool
    executes_parsers: bool
    reads_files: bool
    performs_persistence: bool


@dataclass(frozen=True)
class ParserExecutionRequest:
    """Runtime-passive request describing a future parser invocation."""

    parser_run_id: str
    source_family: str
    source_document_id: str
    source_document_uri: str
    source_checksum_sha256: str | None
    parser_key: str
    parser_source_format: ParserSourceFormat
    parser_run_status: ParserRunStatus
    execution_status: ParserExecutionBoundaryStatus
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class ParserExecutionBoundaryResult:
    """Deterministic parser execution boundary contract result."""

    status: ParserExecutionBoundaryStatus
    mode: SourceAcquisitionPlanMode
    descriptor: ParserExecutionBoundaryDescriptor
    selected_source_families: tuple[str, ...]
    requests: tuple[ParserExecutionRequest, ...]


def create_phase1_parser_execution_boundary(
    selection_result: ParserSelectionResult | None = None,
    run_contract: ParserRunContractResult | None = None,
) -> ParserExecutionBoundaryResult:
    """Create future parser invocation requests without executing parsers."""

    active_selection = select_phase1_parsers() if selection_result is None else selection_result
    active_run_contract = (
        create_phase1_parser_run_contract() if run_contract is None else run_contract
    )
    if active_selection.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run parser execution selections are supported.")
    if active_run_contract.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run parser run contracts are supported.")

    run_requests_by_document_id = {
        request.source_document_id: request
        for request in active_run_contract.requests
    }
    requests = tuple(
        _create_execution_request(
            selection=selection,
            run_request=run_requests_by_document_id[selection.source_document_id],
        )
        for selection in active_selection.selections
    )

    return ParserExecutionBoundaryResult(
        status=ParserExecutionBoundaryStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        descriptor=ParserExecutionBoundaryDescriptor(
            mode=SourceAcquisitionPlanMode.DRY_RUN,
            status=ParserExecutionBoundaryStatus.PLANNED,
            instantiates_parsers=False,
            executes_parsers=False,
            reads_files=False,
            performs_persistence=False,
        ),
        selected_source_families=active_selection.selected_source_families,
        requests=requests,
    )


def _create_execution_request(
    *,
    selection: ParserSelection,
    run_request: ParserRunRequest,
) -> ParserExecutionRequest:
    if selection.source_family != run_request.source_family:
        raise ValueError("parser selection source_family must match parser run request.")
    if selection.source_document_uri != run_request.source_document_uri:
        raise ValueError(
            "parser selection source_document_uri must match parser run request."
        )

    return ParserExecutionRequest(
        parser_run_id=run_request.parser_run_id,
        source_family=selection.source_family,
        source_document_id=selection.source_document_id,
        source_document_uri=selection.source_document_uri,
        source_checksum_sha256=run_request.source_checksum_sha256,
        parser_key=selection.parser_key,
        parser_source_format=selection.parser_source_format,
        parser_run_status=run_request.parser_status,
        execution_status=ParserExecutionBoundaryStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )
