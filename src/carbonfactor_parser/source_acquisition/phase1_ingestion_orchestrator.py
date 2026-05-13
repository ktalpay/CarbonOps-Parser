"""Explicit Phase 1 ingestion orchestrator with injected runtime boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol, Sequence, runtime_checkable

from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunResult,
    ParserRunStatus,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    create_parser_normalized_output_batch,
)
from carbonfactor_parser.parsers.run_repository_contract import (
    ParserRunRepository,
    ParserRunRepositoryPersistStatus,
)
from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    ParsedFactorPersistenceStatus,
    ParsedFactorPersistenceWriterResult,
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_runtime_config_gate import (
    PostgreSQLRuntimeConfigGateDecision,
)
from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
    PostgreSQLSchemaBootstrapReport,
)
from carbonfactor_parser.persistence.source_document_repository import (
    SourceDocumentRepository,
    SourceDocumentRepositoryPersistStatus,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyRepository,
)
from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidateResult,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentChecksumStatus,
    SourceDocumentPersistenceMappingStatus,
    SourceDocumentPersistenceRecord,
)
from carbonfactor_parser.source_acquisition.phase1_observability import (
    emit_phase1_operational_event,
    summarize_phase1_family_result_for_diagnostics,
    summarize_phase1_orchestrator_request,
    summarize_phase1_orchestrator_result_for_diagnostics,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    SourceAcquisitionRunResult,
    SourceAcquisitionRunStatus,
)
from carbonfactor_parser.source_acquisition.run_repository_contract import (
    SourceAcquisitionRunRepository,
    SourceAcquisitionRunRepositoryPersistStatus,
)


PHASE1_SOURCE_FAMILIES = ("ghg_protocol", "defra_desnz", "ipcc_efdb")
_SOURCE_FAMILY_ALIASES: Mapping[str, str] = {
    "ghg": "ghg_protocol",
    "ghg_protocol": "ghg_protocol",
    "defra": "defra_desnz",
    "desnz": "defra_desnz",
    "defra_desnz": "defra_desnz",
    "ipcc": "ipcc_efdb",
    "ipcc_efdb": "ipcc_efdb",
}


class Phase1IngestionExecutionMode(str, Enum):
    """Execution modes exposed by the orchestrator."""

    SEQUENTIAL = "sequential"
    BOUNDED_PARALLEL = "bounded_parallel"


class Phase1IngestionRunStatus(str, Enum):
    """Top-level Phase 1 ingestion run status."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    FAILED = "failed"
    NOT_EXECUTABLE = "not_executable"


class Phase1IngestionFamilyStatus(str, Enum):
    """Per-source-family deterministic status."""

    COMPLETED = "completed"
    FAILED_DISCOVERY = "failed_discovery"
    FAILED_DOWNLOAD = "failed_download"
    FAILED_SOURCE_RUN_PERSISTENCE = "failed_source_run_persistence"
    FAILED_SOURCE_DOCUMENT_PERSISTENCE = "failed_source_document_persistence"
    FAILED_PARSER = "failed_parser"
    FAILED_PARSER_RUN_PERSISTENCE = "failed_parser_run_persistence"
    FAILED_PARSED_FACTOR_PERSISTENCE = "failed_parsed_factor_persistence"


@dataclass(frozen=True)
class Phase1IngestionFailureDetail:
    """Structured failure detail recorded by the orchestrator."""

    source_family: str | None
    stage: str
    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class Phase1IngestionRunSummary:
    """Success/failure counts for a Phase 1 ingestion run."""

    requested_family_count: int
    completed_family_count: int
    failed_family_count: int
    source_candidate_count: int
    source_artifact_count: int
    parser_run_count: int
    parsed_factor_row_count: int
    persisted_source_run_count: int
    persisted_source_document_count: int
    persisted_parser_run_count: int
    persisted_master_count: int
    persisted_detail_count: int
    failure_count: int


@dataclass(frozen=True)
class Phase1SourceFamilyIngestionResult:
    """Recorded state for one source-family ingestion execution."""

    source_family: str
    status: Phase1IngestionFamilyStatus
    discovery_result: SourceDiscoveryCandidateResult | None = None
    acquisition_result: SourceAcquisitionRunResult | None = None
    parser_run_result: ParserRunResult | None = None
    parsed_factor_persistence_result: ParsedFactorPersistenceWriterResult | None = None
    persisted_source_run_count: int = 0
    persisted_source_document_count: int = 0
    persisted_parser_run_count: int = 0
    persisted_master_count: int = 0
    persisted_detail_count: int = 0
    failures: tuple[Phase1IngestionFailureDetail, ...] = ()


@dataclass(frozen=True)
class Phase1IngestionOrchestratorRequest:
    """Explicit request for Phase 1 source-family ingestion."""

    source_families: tuple[str, ...]
    run_id: str
    correlation_id: str | None = None
    execution_mode: Phase1IngestionExecutionMode = (
        Phase1IngestionExecutionMode.SEQUENTIAL
    )
    max_parallelism: int = 1
    runtime_config_decision: PostgreSQLRuntimeConfigGateDecision | None = None
    schema_bootstrap_report: PostgreSQLSchemaBootstrapReport | None = None


@dataclass(frozen=True)
class Phase1IngestionOrchestratorResult:
    """End-to-end Phase 1 ingestion result."""

    status: Phase1IngestionRunStatus
    request: Phase1IngestionOrchestratorRequest
    selected_source_families: tuple[str, ...]
    family_results: tuple[Phase1SourceFamilyIngestionResult, ...]
    summary: Phase1IngestionRunSummary
    failures: tuple[Phase1IngestionFailureDetail, ...] = ()


@runtime_checkable
class Phase1SourceFamilyRuntime(Protocol):
    """Injected source-family runtime used by tests or reviewed adapters."""

    def discover(
        self,
        source_family: str,
        request: Phase1IngestionOrchestratorRequest,
    ) -> SourceDiscoveryCandidateResult:
        """Discover candidate source documents for one family."""

    def download(
        self,
        source_family: str,
        discovery_result: SourceDiscoveryCandidateResult,
        request: Phase1IngestionOrchestratorRequest,
    ) -> SourceAcquisitionRunResult:
        """Download candidate documents for one family."""

    def parse(
        self,
        source_family: str,
        acquisition_result: SourceAcquisitionRunResult,
        request: Phase1IngestionOrchestratorRequest,
    ) -> ParserRunResult:
        """Normalize downloaded artifacts into parser rows."""


@dataclass(frozen=True)
class Phase1IngestionOrchestratorDependencies:
    """Injected runtime dependencies for safe orchestration tests/adapters."""

    source_runtimes: Mapping[str, Phase1SourceFamilyRuntime]
    source_run_repository: SourceAcquisitionRunRepository
    source_document_repository: SourceDocumentRepository
    parser_run_repository: ParserRunRepository
    parsed_factor_repository: SourceFamilyRepository


def run_phase1_ingestion_orchestrator(
    request: Phase1IngestionOrchestratorRequest,
    dependencies: Phase1IngestionOrchestratorDependencies,
) -> Phase1IngestionOrchestratorResult:
    """Run Phase 1 ingestion sequentially with all runtime work injected."""

    emit_phase1_operational_event(
        "phase1_ingestion_orchestrator_started",
        summarize_phase1_orchestrator_request(request),
    )
    selected_families, request_failures = _normalize_source_families(
        request.source_families,
    )
    readiness_failures = (
        *request_failures,
        *_execution_mode_failures(request),
        *_postgresql_readiness_failures(request),
    )
    if readiness_failures:
        result = _not_executable_result(request, selected_families, readiness_failures)
        emit_phase1_operational_event(
            "phase1_ingestion_orchestrator_completed",
            summarize_phase1_orchestrator_result_for_diagnostics(result),
        )
        return result

    family_results: list[Phase1SourceFamilyIngestionResult] = []
    for source_family in selected_families:
        emit_phase1_operational_event(
            "phase1_source_family_started",
            {
                "correlation_id": request.correlation_id,
                "run_id": request.run_id,
                "source_family": source_family,
            },
        )
        family_result = _run_source_family(
            source_family=source_family,
            request=request,
            dependencies=dependencies,
        )
        family_results.append(family_result)
        emit_phase1_operational_event(
            "phase1_source_family_completed",
            summarize_phase1_family_result_for_diagnostics(
                family_result,
                run_id=request.run_id,
                correlation_id=request.correlation_id,
            ),
        )

    result = _create_result(request, selected_families, tuple(family_results))
    emit_phase1_operational_event(
        "phase1_ingestion_orchestrator_completed",
        summarize_phase1_orchestrator_result_for_diagnostics(result),
    )
    return result


def _run_source_family(
    *,
    source_family: str,
    request: Phase1IngestionOrchestratorRequest,
    dependencies: Phase1IngestionOrchestratorDependencies,
) -> Phase1SourceFamilyIngestionResult:
    runtime = dependencies.source_runtimes.get(source_family)
    if runtime is None:
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_DISCOVERY,
            _failure(
                source_family,
                "discovery",
                "PHASE1_INGESTION_SOURCE_RUNTIME_MISSING",
                "No source runtime is registered for the selected source family.",
                "source_runtimes",
            ),
        )

    try:
        discovery_result = runtime.discover(source_family, request)
    except Exception as exc:  # noqa: BLE001
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_DISCOVERY,
            _exception_failure(source_family, "discovery", exc),
        )

    try:
        acquisition_result = runtime.download(source_family, discovery_result, request)
    except Exception as exc:  # noqa: BLE001
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_DOWNLOAD,
            _exception_failure(source_family, "download", exc),
            discovery_result=discovery_result,
        )

    if acquisition_result.status is SourceAcquisitionRunStatus.FAILED:
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_DOWNLOAD,
            _failure(
                source_family,
                "download",
                "PHASE1_INGESTION_SOURCE_ACQUISITION_FAILED",
                "Source acquisition returned failed status.",
                "acquisition_result.status",
            ),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
        )

    source_run_persist = dependencies.source_run_repository.persist_runs(
        (acquisition_result,),
    )
    if (
        source_run_persist.status
        is SourceAcquisitionRunRepositoryPersistStatus.FAILED_VALIDATION
    ):
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_SOURCE_RUN_PERSISTENCE,
            _repository_failure(
                source_family,
                "source_run_persistence",
                source_run_persist.issues,
            ),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
        )

    source_document_records = _source_document_records(acquisition_result, request)
    source_document_persist = (
        dependencies.source_document_repository.persist_source_documents(
            source_document_records,
        )
    )
    if (
        source_document_persist.status
        is SourceDocumentRepositoryPersistStatus.FAILED_VALIDATION
    ):
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_SOURCE_DOCUMENT_PERSISTENCE,
            _repository_failure(
                source_family,
                "source_document_persistence",
                source_document_persist.issues,
            ),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
            persisted_source_run_count=source_run_persist.persisted_count,
        )

    try:
        parser_run_result = runtime.parse(source_family, acquisition_result, request)
    except Exception as exc:  # noqa: BLE001
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_PARSER,
            _exception_failure(source_family, "parser", exc),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
            persisted_source_run_count=source_run_persist.persisted_count,
            persisted_source_document_count=source_document_persist.persisted_count,
        )

    if parser_run_result.status is ParserRunStatus.FAILED:
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_PARSER,
            _failure(
                source_family,
                "parser",
                "PHASE1_INGESTION_PARSER_FAILED",
                "Parser run returned failed status.",
                "parser_run_result.status",
            ),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
            parser_run_result=parser_run_result,
            persisted_source_run_count=source_run_persist.persisted_count,
            persisted_source_document_count=source_document_persist.persisted_count,
        )

    parser_run_persist = dependencies.parser_run_repository.persist_runs(
        (parser_run_result,),
    )
    if parser_run_persist.status is ParserRunRepositoryPersistStatus.FAILED_VALIDATION:
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_PARSER_RUN_PERSISTENCE,
            _repository_failure(
                source_family,
                "parser_run_persistence",
                parser_run_persist.issues,
            ),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
            parser_run_result=parser_run_result,
            persisted_source_run_count=source_run_persist.persisted_count,
            persisted_source_document_count=source_document_persist.persisted_count,
        )

    parsed_factor_persist = persist_parsed_factor_records(
        create_parser_normalized_output_batch(parser_run_result.rows),
        dependencies.parsed_factor_repository,
        source_document_id=(
            source_document_records[0].source_document_id
            if source_document_records
            else None
        ),
    )
    if parsed_factor_persist.status is not ParsedFactorPersistenceStatus.DECLARED:
        return _failed_family(
            source_family,
            Phase1IngestionFamilyStatus.FAILED_PARSED_FACTOR_PERSISTENCE,
            _parsed_factor_failure(source_family, parsed_factor_persist),
            discovery_result=discovery_result,
            acquisition_result=acquisition_result,
            parser_run_result=parser_run_result,
            parsed_factor_persistence_result=parsed_factor_persist,
            persisted_source_run_count=source_run_persist.persisted_count,
            persisted_source_document_count=source_document_persist.persisted_count,
            persisted_parser_run_count=parser_run_persist.persisted_count,
        )

    return Phase1SourceFamilyIngestionResult(
        source_family=source_family,
        status=Phase1IngestionFamilyStatus.COMPLETED,
        discovery_result=discovery_result,
        acquisition_result=acquisition_result,
        parser_run_result=parser_run_result,
        parsed_factor_persistence_result=parsed_factor_persist,
        persisted_source_run_count=source_run_persist.persisted_count,
        persisted_source_document_count=source_document_persist.persisted_count,
        persisted_parser_run_count=parser_run_persist.persisted_count,
        persisted_master_count=parsed_factor_persist.persisted_master_count,
        persisted_detail_count=parsed_factor_persist.persisted_detail_count,
    )


def _normalize_source_families(
    source_families: Sequence[str],
) -> tuple[tuple[str, ...], tuple[Phase1IngestionFailureDetail, ...]]:
    selected: list[str] = []
    failures: list[Phase1IngestionFailureDetail] = []
    for position, value in enumerate(source_families):
        normalized = _SOURCE_FAMILY_ALIASES.get(value)
        if normalized is None:
            failures.append(
                _failure(
                    None,
                    "selection",
                    "PHASE1_INGESTION_UNSUPPORTED_SOURCE_FAMILY",
                    "Source family selection must be one of the Phase 1 families.",
                    f"source_families[{position}]",
                )
            )
            continue
        if normalized not in selected:
            selected.append(normalized)

    if not selected:
        failures.append(
            _failure(
                None,
                "selection",
                "PHASE1_INGESTION_EMPTY_SOURCE_FAMILY_SELECTION",
                "At least one Phase 1 source family must be selected explicitly.",
                "source_families",
            )
        )
    return tuple(selected), tuple(failures)


def _execution_mode_failures(
    request: Phase1IngestionOrchestratorRequest,
) -> tuple[Phase1IngestionFailureDetail, ...]:
    if request.execution_mode is Phase1IngestionExecutionMode.SEQUENTIAL:
        if request.max_parallelism != 1:
            return (
                _failure(
                    None,
                    "execution_mode",
                    "PHASE1_INGESTION_SEQUENTIAL_MAX_PARALLELISM_MUST_BE_ONE",
                    "Sequential execution must use max_parallelism=1.",
                    "max_parallelism",
                ),
            )
        return ()

    return (
        _failure(
            None,
            "execution_mode",
            "PHASE1_INGESTION_BOUNDED_PARALLEL_NOT_ENABLED",
            "Bounded parallel execution is a declared extension point only.",
            "execution_mode",
        ),
    )


def _postgresql_readiness_failures(
    request: Phase1IngestionOrchestratorRequest,
) -> tuple[Phase1IngestionFailureDetail, ...]:
    failures: list[Phase1IngestionFailureDetail] = []
    if (
        request.runtime_config_decision is not None
        and not request.runtime_config_decision.runtime_enabled
    ):
        issue = (
            request.runtime_config_decision.issues[0]
            if request.runtime_config_decision.issues
            else None
        )
        failures.append(
            _failure(
                None,
                "postgresql_runtime_config",
                (
                    issue.code
                    if issue is not None
                    else "PHASE1_INGESTION_POSTGRESQL_RUNTIME_NOT_READY"
                ),
                (
                    issue.message
                    if issue is not None
                    else "PostgreSQL runtime configuration is not ready."
                ),
                issue.field_name if issue is not None else "runtime_config_decision",
            )
        )

    if (
        request.schema_bootstrap_report is not None
        and request.schema_bootstrap_report.fail_on_missing
        and request.schema_bootstrap_report.missing_table_names
    ):
        failures.append(
            _failure(
                None,
                "postgresql_schema_bootstrap",
                "PHASE1_INGESTION_POSTGRESQL_SCHEMA_NOT_READY",
                "PostgreSQL schema bootstrap reported missing required tables.",
                "schema_bootstrap_report.missing_table_names",
            )
        )
    return tuple(failures)


def _source_document_records(
    acquisition_result: SourceAcquisitionRunResult,
    request: Phase1IngestionOrchestratorRequest,
) -> tuple[SourceDocumentPersistenceRecord, ...]:
    return tuple(
        SourceDocumentPersistenceRecord(
            source_document_id=(
                f"{request.run_id}_{artifact.source_family}_{artifact.artifact_id}"
            ),
            ingestion_run_id=request.run_id,
            source_family=artifact.source_family,
            source_document_uri=artifact.source_reference_uri,
            source_checksum_sha256=artifact.checksum_sha256,
            checksum_status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
            acquisition_status=SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED,
            acquired_at=None,
            created_at="runtime_timestamp_unavailable",
            updated_at="runtime_timestamp_unavailable",
            logical_document_name=artifact.display_name or artifact.artifact_id,
            target_logical_path=artifact.local_reference,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for artifact in acquisition_result.artifacts
    )


def _create_result(
    request: Phase1IngestionOrchestratorRequest,
    selected_source_families: tuple[str, ...],
    family_results: tuple[Phase1SourceFamilyIngestionResult, ...],
) -> Phase1IngestionOrchestratorResult:
    failures = tuple(
        failure for result in family_results for failure in result.failures
    )
    completed_count = sum(
        1
        for result in family_results
        if result.status is Phase1IngestionFamilyStatus.COMPLETED
    )
    status = (
        Phase1IngestionRunStatus.COMPLETED
        if completed_count == len(family_results)
        else Phase1IngestionRunStatus.COMPLETED_WITH_FAILURES
        if completed_count > 0
        else Phase1IngestionRunStatus.FAILED
    )
    return Phase1IngestionOrchestratorResult(
        status=status,
        request=request,
        selected_source_families=selected_source_families,
        family_results=family_results,
        summary=_summary(request, family_results, failures),
        failures=failures,
    )


def _not_executable_result(
    request: Phase1IngestionOrchestratorRequest,
    selected_source_families: tuple[str, ...],
    failures: tuple[Phase1IngestionFailureDetail, ...],
) -> Phase1IngestionOrchestratorResult:
    return Phase1IngestionOrchestratorResult(
        status=Phase1IngestionRunStatus.NOT_EXECUTABLE,
        request=request,
        selected_source_families=selected_source_families,
        family_results=(),
        summary=Phase1IngestionRunSummary(
            requested_family_count=len(selected_source_families),
            completed_family_count=0,
            failed_family_count=len(selected_source_families),
            source_candidate_count=0,
            source_artifact_count=0,
            parser_run_count=0,
            parsed_factor_row_count=0,
            persisted_source_run_count=0,
            persisted_source_document_count=0,
            persisted_parser_run_count=0,
            persisted_master_count=0,
            persisted_detail_count=0,
            failure_count=len(failures),
        ),
        failures=failures,
    )


def _summary(
    request: Phase1IngestionOrchestratorRequest,
    family_results: tuple[Phase1SourceFamilyIngestionResult, ...],
    failures: tuple[Phase1IngestionFailureDetail, ...],
) -> Phase1IngestionRunSummary:
    return Phase1IngestionRunSummary(
        requested_family_count=len(request.source_families),
        completed_family_count=sum(
            1
            for result in family_results
            if result.status is Phase1IngestionFamilyStatus.COMPLETED
        ),
        failed_family_count=sum(
            1
            for result in family_results
            if result.status is not Phase1IngestionFamilyStatus.COMPLETED
        ),
        source_candidate_count=sum(
            len(result.discovery_result.candidates)
            for result in family_results
            if result.discovery_result is not None
        ),
        source_artifact_count=sum(
            len(result.acquisition_result.artifacts)
            for result in family_results
            if result.acquisition_result is not None
        ),
        parser_run_count=sum(
            1 for result in family_results if result.parser_run_result is not None
        ),
        parsed_factor_row_count=sum(
            len(result.parser_run_result.rows)
            for result in family_results
            if result.parser_run_result is not None
        ),
        persisted_source_run_count=sum(
            result.persisted_source_run_count for result in family_results
        ),
        persisted_source_document_count=sum(
            result.persisted_source_document_count for result in family_results
        ),
        persisted_parser_run_count=sum(
            result.persisted_parser_run_count for result in family_results
        ),
        persisted_master_count=sum(
            result.persisted_master_count for result in family_results
        ),
        persisted_detail_count=sum(
            result.persisted_detail_count for result in family_results
        ),
        failure_count=len(failures),
    )


def _failed_family(
    source_family: str,
    status: Phase1IngestionFamilyStatus,
    failure: Phase1IngestionFailureDetail,
    *,
    discovery_result: SourceDiscoveryCandidateResult | None = None,
    acquisition_result: SourceAcquisitionRunResult | None = None,
    parser_run_result: ParserRunResult | None = None,
    parsed_factor_persistence_result: ParsedFactorPersistenceWriterResult | None = None,
    persisted_source_run_count: int = 0,
    persisted_source_document_count: int = 0,
    persisted_parser_run_count: int = 0,
) -> Phase1SourceFamilyIngestionResult:
    return Phase1SourceFamilyIngestionResult(
        source_family=source_family,
        status=status,
        discovery_result=discovery_result,
        acquisition_result=acquisition_result,
        parser_run_result=parser_run_result,
        parsed_factor_persistence_result=parsed_factor_persistence_result,
        persisted_source_run_count=persisted_source_run_count,
        persisted_source_document_count=persisted_source_document_count,
        persisted_parser_run_count=persisted_parser_run_count,
        failures=(failure,),
    )


def _failure(
    source_family: str | None,
    stage: str,
    code: str,
    message: str,
    field_name: str | None = None,
) -> Phase1IngestionFailureDetail:
    return Phase1IngestionFailureDetail(
        source_family=source_family,
        stage=stage,
        code=code,
        message=message,
        field_name=field_name,
    )


def _exception_failure(
    source_family: str,
    stage: str,
    exc: Exception,
) -> Phase1IngestionFailureDetail:
    return _failure(
        source_family,
        stage,
        f"PHASE1_INGESTION_{stage.upper()}_EXCEPTION",
        str(exc) or exc.__class__.__name__,
        stage,
    )


def _repository_failure(
    source_family: str,
    stage: str,
    issues: Sequence[object],
) -> Phase1IngestionFailureDetail:
    if issues:
        issue = issues[0]
        return _failure(
            source_family,
            stage,
            str(getattr(issue, "code", "PHASE1_INGESTION_REPOSITORY_FAILED")),
            str(getattr(issue, "message", "Repository persistence failed.")),
            getattr(issue, "field_name", None),
        )
    return _failure(
        source_family,
        stage,
        "PHASE1_INGESTION_REPOSITORY_FAILED",
        "Repository persistence failed without structured issues.",
        stage,
    )


def _parsed_factor_failure(
    source_family: str,
    result: ParsedFactorPersistenceWriterResult,
) -> Phase1IngestionFailureDetail:
    if result.issues:
        issue = result.issues[0]
        return _failure(
            source_family,
            "parsed_factor_persistence",
            issue.code,
            issue.message,
            issue.field_name,
        )
    return _failure(
        source_family,
        "parsed_factor_persistence",
        "PHASE1_INGESTION_PARSED_FACTOR_PERSISTENCE_FAILED",
        "Parsed factor persistence failed without structured issues.",
        "parsed_factor_persistence",
    )
