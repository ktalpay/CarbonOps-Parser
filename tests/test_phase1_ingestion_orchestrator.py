from __future__ import annotations

import json
import logging
from decimal import Decimal

from carbonfactor_parser.parsers.input_artifact_contract import (
    create_phase1_parser_input_artifact,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputRowStatus,
    create_parser_normalized_output_row,
)
from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunResult,
    ParserRunStatus,
    create_parser_run_request,
    create_parser_run_result,
)
from carbonfactor_parser.parsers.run_repository_contract import (
    create_parser_run_repository_persist_result,
)
from carbonfactor_parser.persistence.source_document_repository import (
    SourceDocumentRepositoryIssue,
    create_source_document_repository_persist_result,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    create_source_family_repository_persist_result,
)
from carbonfactor_parser.persistence.postgresql_runtime_config_gate import (
    PostgreSQLRuntimeConfigGate,
    evaluate_postgresql_runtime_config_gate,
)
from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
    build_postgresql_phase1_schema_bootstrap_report,
)
from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidate,
    SourceDiscoveryCandidateResult,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    create_source_download_artifact_from_candidate,
)
from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
    PHASE1_SOURCE_FAMILIES,
    Phase1IngestionExecutionMode,
    Phase1IngestionFamilyStatus,
    Phase1IngestionOrchestratorDependencies,
    Phase1IngestionOrchestratorRequest,
    Phase1IngestionRunStatus,
    run_phase1_ingestion_orchestrator,
)
from carbonfactor_parser.source_acquisition.phase1_observability import (
    PHASE1_OPERATIONAL_LOGGER_NAME,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    SourceAcquisitionRunSummary,
    SourceAcquisitionRunResult,
    SourceAcquisitionRunStatus,
)
from carbonfactor_parser.source_acquisition.run_repository_contract import (
    create_source_acquisition_run_repository_persist_result,
)


def test_orchestrator_runs_selected_phase1_families_end_to_end_sequentially() -> None:
    dependencies = _dependencies(
        {
            source_family: _FakeSourceRuntime(source_family)
            for source_family in PHASE1_SOURCE_FAMILIES
        }
    )

    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ghg", "defra_desnz", "ipcc_efdb"),
            run_id="phase1-run-001",
        ),
        dependencies,
    )

    assert result.status is Phase1IngestionRunStatus.COMPLETED
    assert result.selected_source_families == PHASE1_SOURCE_FAMILIES
    assert [family.source_family for family in result.family_results] == list(
        PHASE1_SOURCE_FAMILIES
    )
    assert all(
        family.status is Phase1IngestionFamilyStatus.COMPLETED
        for family in result.family_results
    )
    assert result.summary.completed_family_count == 3
    assert result.summary.failed_family_count == 0
    assert result.summary.source_candidate_count == 3
    assert result.summary.source_artifact_count == 3
    assert result.summary.parser_run_count == 3
    assert result.summary.parsed_factor_row_count == 3
    assert result.summary.persisted_source_run_count == 3
    assert result.summary.persisted_source_document_count == 3
    assert result.summary.persisted_parser_run_count == 3
    assert result.summary.persisted_master_count == 3
    assert result.summary.persisted_detail_count == 3
    assert result.failures == ()


def test_orchestrator_emits_correlation_friendly_operational_logs(caplog) -> None:
    dependencies = _dependencies({"ghg_protocol": _FakeSourceRuntime("ghg_protocol")})

    with caplog.at_level(logging.INFO, logger=PHASE1_OPERATIONAL_LOGGER_NAME):
        run_phase1_ingestion_orchestrator(
            Phase1IngestionOrchestratorRequest(
                source_families=("ghg_protocol",),
                run_id="phase1-run-009",
                correlation_id="correlation-009",
            ),
            dependencies,
        )

    events = [json.loads(record.message) for record in caplog.records]

    assert tuple(event["event"] for event in events) == (
        "phase1_ingestion_orchestrator_started",
        "phase1_source_family_started",
        "phase1_source_family_completed",
        "phase1_ingestion_orchestrator_completed",
    )
    family_completed = events[2]
    assert family_completed["run_id"] == "phase1-run-009"
    assert family_completed["correlation_id"] == "correlation-009"
    assert family_completed["source_family"] == "ghg_protocol"
    assert family_completed["source_key"] == "ghg_protocol"
    assert family_completed["parser"]["accepted_row_count"] == 1
    assert family_completed["parser"]["validation_issue_count"] == 0
    assert family_completed["parser"]["failure_count"] == 0
    assert family_completed["persistence"] == {
        "parsed_factor_detail_count": 1,
        "parsed_factor_master_count": 1,
        "parser_run_count": 1,
        "source_document_count": 1,
        "source_run_count": 1,
    }
    assert family_completed["documents"] == [
        {
            "checksum_sha256": None,
            "document_id": "ghg_protocol-artifact",
            "source_family": "ghg_protocol",
            "source_key": "ghg_protocol",
        },
    ]


def test_orchestrator_failure_log_uses_structured_reason_codes(caplog) -> None:
    dependencies = _dependencies(
        {
            "defra_desnz": _FakeSourceRuntime(
                "defra_desnz",
                parser_status=ParserRunStatus.FAILED,
            ),
        }
    )

    with caplog.at_level(logging.INFO, logger=PHASE1_OPERATIONAL_LOGGER_NAME):
        run_phase1_ingestion_orchestrator(
            Phase1IngestionOrchestratorRequest(
                source_families=("defra_desnz",),
                run_id="phase1-run-010",
            ),
            dependencies,
        )

    family_completed = [
        json.loads(record.message)
        for record in caplog.records
        if json.loads(record.message)["event"] == "phase1_source_family_completed"
    ][0]

    assert family_completed["status"] == "failed_parser"
    assert family_completed["failures"] == [
        {
            "code": "PHASE1_INGESTION_PARSER_FAILED",
            "field_name": "parser_run_result.status",
            "message": "Parser run returned failed status.",
            "severity": "error",
            "source_family": "defra_desnz",
            "source_key": "defra_desnz",
            "stage": "parser",
        },
    ]


def test_orchestrator_only_runs_explicitly_selected_source_family() -> None:
    runtimes = {
        source_family: _FakeSourceRuntime(source_family)
        for source_family in PHASE1_SOURCE_FAMILIES
    }
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("defra",),
            run_id="phase1-run-002",
        ),
        _dependencies(runtimes),
    )

    assert result.status is Phase1IngestionRunStatus.COMPLETED
    assert result.selected_source_families == ("defra_desnz",)
    assert result.family_results[0].acquisition_result is not None
    assert result.family_results[0].acquisition_result.run_id == "phase1-run-002"
    assert runtimes["defra_desnz"].calls == ("discover", "download", "parse")
    assert runtimes["ghg_protocol"].calls == ()
    assert runtimes["ipcc_efdb"].calls == ()


def test_duplicate_source_family_selection_is_idempotent() -> None:
    runtime = _FakeSourceRuntime("ipcc_efdb")

    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ipcc", "ipcc_efdb"),
            run_id="phase1-run-008",
        ),
        _dependencies({"ipcc_efdb": runtime}),
    )

    assert result.status is Phase1IngestionRunStatus.COMPLETED
    assert result.selected_source_families == ("ipcc_efdb",)
    assert len(result.family_results) == 1
    assert runtime.calls == ("discover", "download", "parse")


def test_partial_failure_is_deterministic_per_source_family() -> None:
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ghg_protocol", "defra_desnz", "ipcc_efdb"),
            run_id="phase1-run-003",
        ),
        _dependencies(
            {
                "ghg_protocol": _FakeSourceRuntime("ghg_protocol"),
                "defra_desnz": _FakeSourceRuntime(
                    "defra_desnz",
                    parser_status=ParserRunStatus.FAILED,
                ),
                "ipcc_efdb": _FakeSourceRuntime("ipcc_efdb"),
            }
        ),
    )

    assert result.status is Phase1IngestionRunStatus.COMPLETED_WITH_FAILURES
    assert tuple(family.status for family in result.family_results) == (
        Phase1IngestionFamilyStatus.COMPLETED,
        Phase1IngestionFamilyStatus.FAILED_PARSER,
        Phase1IngestionFamilyStatus.COMPLETED,
    )
    assert result.summary.completed_family_count == 2
    assert result.summary.failed_family_count == 1
    assert result.summary.failure_count == 1
    assert result.failures[0].source_family == "defra_desnz"
    assert result.failures[0].stage == "parser"
    assert result.failures[0].code == "PHASE1_INGESTION_PARSER_FAILED"


def test_bounded_parallel_is_declared_but_not_enabled_by_default() -> None:
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ghg_protocol",),
            run_id="phase1-run-004",
            execution_mode=Phase1IngestionExecutionMode.BOUNDED_PARALLEL,
            max_parallelism=2,
        ),
        _dependencies({"ghg_protocol": _FakeSourceRuntime("ghg_protocol")}),
    )

    assert result.status is Phase1IngestionRunStatus.NOT_EXECUTABLE
    assert result.family_results == ()
    assert result.failures[0].code == "PHASE1_INGESTION_BOUNDED_PARALLEL_NOT_ENABLED"


def test_postgresql_runtime_readiness_blocks_before_source_execution() -> None:
    runtime = _FakeSourceRuntime("ghg_protocol")
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ghg_protocol",),
            run_id="phase1-run-006",
            runtime_config_decision=evaluate_postgresql_runtime_config_gate(
                PostgreSQLRuntimeConfigGate(requested=True),
            ),
        ),
        _dependencies({"ghg_protocol": runtime}),
    )

    assert result.status is Phase1IngestionRunStatus.NOT_EXECUTABLE
    assert result.family_results == ()
    assert runtime.calls == ()
    assert result.failures[0].stage == "postgresql_runtime_config"
    assert result.failures[0].code == "POSTGRESQL_RUNTIME_CONFIG_BLOCKED"


def test_postgresql_schema_bootstrap_missing_tables_blocks_execution() -> None:
    runtime = _FakeSourceRuntime("ghg_protocol")
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ghg_protocol",),
            run_id="phase1-run-007",
            schema_bootstrap_report=build_postgresql_phase1_schema_bootstrap_report(),
        ),
        _dependencies({"ghg_protocol": runtime}),
    )

    assert result.status is Phase1IngestionRunStatus.NOT_EXECUTABLE
    assert result.family_results == ()
    assert runtime.calls == ()
    assert result.failures[0].stage == "postgresql_schema_bootstrap"
    assert result.failures[0].code == "PHASE1_INGESTION_POSTGRESQL_SCHEMA_NOT_READY"


def test_repository_failure_stops_family_at_deterministic_stage() -> None:
    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=("ipcc_efdb",),
            run_id="phase1-run-005",
        ),
        _dependencies(
            {"ipcc_efdb": _FakeSourceRuntime("ipcc_efdb")},
            fail_source_documents=True,
        ),
    )

    family = result.family_results[0]
    assert result.status is Phase1IngestionRunStatus.FAILED
    assert family.status is (
        Phase1IngestionFamilyStatus.FAILED_SOURCE_DOCUMENT_PERSISTENCE
    )
    assert family.parser_run_result is None
    assert result.failures[0].stage == "source_document_persistence"
    assert result.failures[0].code == "SOURCE_DOCUMENT_REPOSITORY_TEST_FAILURE"


class _FakeSourceRuntime:
    def __init__(
        self,
        source_family: str,
        *,
        parser_status: ParserRunStatus = ParserRunStatus.COMPLETED,
    ) -> None:
        self.source_family = source_family
        self.parser_status = parser_status
        self.calls: tuple[str, ...] = ()

    def discover(
        self,
        source_family: str,
        request: Phase1IngestionOrchestratorRequest,
    ) -> SourceDiscoveryCandidateResult:
        self.calls = (*self.calls, "discover")
        return SourceDiscoveryCandidateResult(
            candidates=(
                SourceDiscoveryCandidate(
                    source_family=source_family,
                    source_key=source_family,
                    candidate_id=f"{source_family}-candidate",
                    title=f"{source_family} fixture",
                    reference_uri=f"fixture://{source_family}/source.csv",
                    artifact_kind="csv",
                    reporting_year=2024,
                    content_type="text/csv",
                    extension=".csv",
                    version_label="fixture",
                ),
            )
        )

    def download(
        self,
        source_family: str,
        discovery_result: SourceDiscoveryCandidateResult,
        request: Phase1IngestionOrchestratorRequest,
    ) -> SourceAcquisitionRunResult:
        self.calls = (*self.calls, "download")
        artifact = create_source_download_artifact_from_candidate(
            discovery_result.candidates[0],
            artifact_id=f"{source_family}-artifact",
            local_reference=f"fixture://{source_family}/downloaded.csv",
            content_type="text/csv",
            extension=".csv",
        )
        return SourceAcquisitionRunResult(
            source_family=source_family,
            source_key=source_family,
            status=SourceAcquisitionRunStatus.COMPLETED,
            candidates=discovery_result.candidates,
            artifacts=(artifact,),
            issues=(),
            summary=SourceAcquisitionRunSummary(
                candidate_count=1,
                artifact_count=1,
                issue_count=0,
                info_count=0,
                warning_count=0,
                error_count=0,
            ),
            run_id=request.run_id,
            version_label="fixture",
        )

    def parse(
        self,
        source_family: str,
        acquisition_result: SourceAcquisitionRunResult,
        request: Phase1IngestionOrchestratorRequest,
    ) -> ParserRunResult:
        self.calls = (*self.calls, "parse")
        artifact = create_phase1_parser_input_artifact(
            source_family=source_family,
            artifact_reference=acquisition_result.artifacts[0].local_reference,
            reporting_year=2024,
        )
        parser_request = create_parser_run_request(
            source_family=source_family,
            artifacts=(artifact,),
            run_id=f"{request.run_id}-{source_family}-parser",
            correlation_id=request.correlation_id,
        )
        rows = ()
        if self.parser_status is not ParserRunStatus.FAILED:
            rows = (
                create_parser_normalized_output_row(
                    artifact=artifact,
                    row_id=f"{source_family}-row-001",
                    status=ParserNormalizedOutputRowStatus.DECLARED,
                    normalized_fields={
                        "source_document_id": f"{source_family}-artifact",
                        "source_year": 2024,
                        "source_version": "fixture",
                        "factor_id": f"{source_family}-factor",
                        "factor_value": Decimal("1.0"),
                        "factor_unit": "kg CO2e",
                    },
                ),
            )
        return create_parser_run_result(
            request=parser_request,
            status=self.parser_status,
            rows=rows,
        )


class _FakeSourceRunRepository:
    @property
    def provider_name(self) -> str:
        return "fake_source_runs"

    def persist_runs(self, runs):
        return create_source_acquisition_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=tuple(runs),
        )


class _FakeSourceDocumentRepository:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    @property
    def provider_name(self) -> str:
        return "fake_source_documents"

    def persist_source_documents(self, records):
        issues = ()
        if self.fail:
            issues = (
                SourceDocumentRepositoryIssue(
                    code="SOURCE_DOCUMENT_REPOSITORY_TEST_FAILURE",
                    message="source document persistence failed",
                    field_name="records",
                ),
            )
        return create_source_document_repository_persist_result(
            provider_name=self.provider_name,
            records=tuple(records),
            issues=issues,
        )


class _FakeParserRunRepository:
    @property
    def provider_name(self) -> str:
        return "fake_parser_runs"

    def persist_runs(self, runs):
        return create_parser_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=tuple(runs),
        )


class _FakeSourceFamilyRepository:
    @property
    def provider_name(self) -> str:
        return "fake_source_family"

    def persist_source_family_records(
        self,
        master_records: tuple[SourceFamilyMasterRecord, ...],
        detail_records: tuple[SourceFamilyDetailRecord, ...],
    ):
        return create_source_family_repository_persist_result(
            provider_name=self.provider_name,
            master_records=master_records,
            detail_records=detail_records,
        )


def _dependencies(
    runtimes,
    *,
    fail_source_documents: bool = False,
) -> Phase1IngestionOrchestratorDependencies:
    return Phase1IngestionOrchestratorDependencies(
        source_runtimes=runtimes,
        source_run_repository=_FakeSourceRunRepository(),
        source_document_repository=_FakeSourceDocumentRepository(
            fail=fail_source_documents,
        ),
        parser_run_repository=_FakeParserRunRepository(),
        parsed_factor_repository=_FakeSourceFamilyRepository(),
    )
