from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputBatch,
    ParserNormalizedOutputRow,
    ParserNormalizedOutputRowStatus,
    create_parser_normalized_output_batch,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    PRODUCTION_E2E_SOURCE_FAMILIES,
    ProductionE2EDownloadedArtifact,
    ProductionE2ESourceYearDiscoveryRequest,
    ProductionE2ESourceYearDiscoveryResult,
    ProductionE2ESourceYearDiscoveryStatus,
    ProductionE2ESourceYearDownloadResult,
    ProductionE2ESourceYearDownloadStatus,
    ProductionE2EValidationResult,
    ProductionE2EValidationStatus,
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorDependencies,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearRunStatus,
    ProductionE2EYearSelectionStatus,
    run_production_e2e_year_orchestrator,
)


def test_first_run_without_existing_data_targets_default_2024() -> None:
    year_state = _FakeYearStateRepository()
    adapter = _FakeSourceAdapter("ghg_protocol", available_years=(2024,))
    parser = _FakeParser()
    insert_repository = _FakeInsertRepository()

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="production-e2e-run-001",
            enabled_source_families=("ghg_protocol",),
        ),
        _dependencies(
            year_state,
            {"ghg_protocol": adapter},
            {"ghg_protocol": parser},
            insert_repository,
        ),
    )

    family = result.family_results[0]
    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert family.status is ProductionE2EYearFamilyStatus.COMPLETED
    assert family.year_state.latest_year is None
    assert family.year_state.target_year == 2024
    assert family.year_state.selection_status is (
        ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED
    )
    assert adapter.discovery_requests[0].target_year == 2024
    assert parser.parsed_artifacts[0].source_year == 2024
    assert insert_repository.inserted_batches[0].row_count == 1
    assert year_state.recorded_years == (("ghg", 2024),)


def test_next_run_after_2024_targets_2025() -> None:
    year_state = _FakeYearStateRepository({"defra": 2024})
    adapter = _FakeSourceAdapter("defra_desnz", available_years=(2025,))

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="production-e2e-run-002",
            enabled_source_families=("defra_desnz",),
        ),
        _dependencies(year_state, {"defra_desnz": adapter}),
    )

    family = result.family_results[0]
    assert family.status is ProductionE2EYearFamilyStatus.COMPLETED
    assert family.year_state.latest_year == 2024
    assert family.year_state.target_year == 2025
    assert family.year_state.selection_status is (
        ProductionE2EYearSelectionStatus.NEXT_YEAR_SELECTED
    )
    assert adapter.discovery_requests[0].target_year == 2025
    assert year_state.recorded_years == (("defra", 2025),)


def test_next_run_after_2025_targets_2026() -> None:
    year_state = _FakeYearStateRepository({"ipcc": 2025})
    adapter = _FakeSourceAdapter("ipcc_efdb", available_years=(2026,))

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="production-e2e-run-003",
            enabled_source_families=("ipcc_efdb",),
        ),
        _dependencies(year_state, {"ipcc_efdb": adapter}),
    )

    family = result.family_results[0]
    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert family.year_state.latest_year == 2025
    assert family.year_state.target_year == 2026
    assert adapter.discovery_requests[0].target_year == 2026
    assert year_state.recorded_years == (("ipcc", 2026),)


def test_next_run_after_2026_reports_2027_unavailable_as_safe_noop() -> None:
    year_state = _FakeYearStateRepository({"ghg": 2026})
    adapter = _FakeSourceAdapter("ghg_protocol", available_years=())
    parser = _FakeParser()
    insert_repository = _FakeInsertRepository()

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="production-e2e-run-004",
            enabled_source_families=("ghg_protocol",),
        ),
        _dependencies(
            year_state,
            {"ghg_protocol": adapter},
            {"ghg_protocol": parser},
            insert_repository,
        ),
    )

    family = result.family_results[0]
    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert family.status is ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR
    assert family.year_state.latest_year == 2026
    assert family.year_state.target_year == 2027
    assert family.discovery_result is not None
    assert family.discovery_result.status is (
        ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR
    )
    assert parser.parsed_artifacts == ()
    assert insert_repository.inserted_batches == ()
    assert year_state.recorded_years == ()
    assert result.summary.no_available_source_year_count == 1
    assert result.summary.failed_family_count == 0


def test_all_three_source_families_are_represented_in_one_run_summary() -> None:
    year_state = _FakeYearStateRepository()
    adapters = {
        source_family: _FakeSourceAdapter(source_family, available_years=(2024,))
        for source_family in PRODUCTION_E2E_SOURCE_FAMILIES
    }
    parsers = {
        source_family: _FakeParser()
        for source_family in PRODUCTION_E2E_SOURCE_FAMILIES
    }
    insert_repository = _FakeInsertRepository()

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(run_id="production-e2e-run-005"),
        _dependencies(year_state, adapters, parsers, insert_repository),
    )

    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert result.selected_source_families == PRODUCTION_E2E_SOURCE_FAMILIES
    assert tuple(family.source_family for family in result.family_results) == (
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    )
    assert tuple(family.year_state.target_year for family in result.family_results) == (
        2024,
        2024,
        2024,
    )
    assert result.summary.requested_family_count == 3
    assert result.summary.completed_family_count == 3
    assert result.summary.no_available_source_year_count == 0
    assert result.summary.failed_family_count == 0
    assert result.summary.parsed_row_count == 3
    assert result.summary.attempted_insert_count == 3
    assert result.summary.inserted_count == 3
    assert year_state.recorded_years == (
        ("ghg", 2024),
        ("defra", 2024),
        ("ipcc", 2024),
    )


class _FakeYearStateRepository:
    def __init__(self, latest_years: dict[str, int] | None = None) -> None:
        self.latest_years = dict(latest_years or {})
        self._recorded_years: list[tuple[str, int]] = []

    @property
    def recorded_years(self) -> tuple[tuple[str, int], ...]:
        return tuple(self._recorded_years)

    def latest_ingested_year(self, source_family: str) -> int | None:
        return self.latest_years.get(source_family)

    def record_ingested_year(self, source_family: str, ingested_year: int) -> None:
        self.latest_years[source_family] = ingested_year
        self._recorded_years.append((source_family, ingested_year))


class _FakeSourceAdapter:
    def __init__(self, source_family: str, *, available_years: tuple[int, ...]) -> None:
        self._source_family = source_family
        self.available_years = set(available_years)
        self._discovery_requests: list[ProductionE2ESourceYearDiscoveryRequest] = []

    @property
    def source_family(self) -> str:
        return self._source_family

    @property
    def discovery_requests(
        self,
    ) -> tuple[ProductionE2ESourceYearDiscoveryRequest, ...]:
        return tuple(self._discovery_requests)

    def discover_target_year(
        self,
        request: ProductionE2ESourceYearDiscoveryRequest,
    ) -> ProductionE2ESourceYearDiscoveryResult:
        self._discovery_requests.append(request)
        if request.target_year not in self.available_years:
            return ProductionE2ESourceYearDiscoveryResult(
                status=ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR,
                source_family=request.source_family,
                target_year=request.target_year,
                reason_code="target_year_not_published",
            )
        return ProductionE2ESourceYearDiscoveryResult(
            status=ProductionE2ESourceYearDiscoveryStatus.SOURCE_YEAR_AVAILABLE,
            source_family=request.source_family,
            target_year=request.target_year,
            artifact_reference=(
                f"local://{request.source_family}/{request.target_year}.csv"
            ),
        )

    def download_target_year(
        self,
        discovery_result: ProductionE2ESourceYearDiscoveryResult,
    ) -> ProductionE2ESourceYearDownloadResult:
        assert discovery_result.artifact_reference is not None
        return ProductionE2ESourceYearDownloadResult(
            status=ProductionE2ESourceYearDownloadStatus.DOWNLOADED,
            source_family=discovery_result.source_family,
            target_year=discovery_result.target_year,
            artifact=ProductionE2EDownloadedArtifact(
                source_family=discovery_result.source_family,
                source_year=discovery_result.target_year,
                artifact_reference=discovery_result.artifact_reference,
                checksum_sha256="fake-checksum",
                content_type="text/csv",
                format_hint="csv",
            ),
        )


class _FakeParser:
    def __init__(self) -> None:
        self._parsed_artifacts: list[ProductionE2EDownloadedArtifact] = []

    @property
    def parsed_artifacts(self) -> tuple[ProductionE2EDownloadedArtifact, ...]:
        return tuple(self._parsed_artifacts)

    def parse(
        self,
        artifact: ProductionE2EDownloadedArtifact,
    ) -> ParserNormalizedOutputBatch:
        self._parsed_artifacts.append(artifact)
        return create_parser_normalized_output_batch(
            (
                ParserNormalizedOutputRow(
                    source_family=artifact.source_family,
                    source_key=artifact.source_family,
                    parser_key=f"{artifact.source_family}_parser",
                    artifact_reference=artifact.artifact_reference,
                    row_id=f"{artifact.source_family}-{artifact.source_year}-1",
                    normalized_fields=(
                        ("source_family", artifact.source_family),
                        ("source_id", artifact.source_family),
                        ("factor_id", "factor-1"),
                        ("factor_name", "Example factor"),
                        ("factor_value", "1.0"),
                        ("unit", "kg CO2e"),
                    ),
                    status=ParserNormalizedOutputRowStatus.VALIDATED,
                    reporting_year=artifact.source_year,
                ),
            )
        )


class _FakeValidationBoundary:
    def validate(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> ProductionE2EValidationResult:
        return ProductionE2EValidationResult(
            status=ProductionE2EValidationStatus.VALIDATED,
            diagnostic_count=0,
            blocking_error_count=0,
            warning_count=0,
        )


@dataclass(frozen=True)
class _FakeInsertResult:
    status: str
    attempted: int
    inserted: int
    skipped_duplicate: int = 0
    failed: int = 0
    validation_error_count: int = 0


class _FakeInsertRepository:
    def __init__(self) -> None:
        self._inserted_batches: list[ParserNormalizedOutputBatch] = []

    @property
    def inserted_batches(self) -> tuple[ParserNormalizedOutputBatch, ...]:
        return tuple(self._inserted_batches)

    def insert_normalized_factor_records(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> _FakeInsertResult:
        self._inserted_batches.append(batch)
        return _FakeInsertResult(
            status="inserted",
            attempted=batch.row_count,
            inserted=batch.row_count,
        )


def _dependencies(
    year_state: _FakeYearStateRepository,
    adapters: dict[str, _FakeSourceAdapter],
    parsers: dict[str, _FakeParser] | None = None,
    insert_repository: _FakeInsertRepository | None = None,
) -> ProductionE2EYearOrchestratorDependencies:
    active_parsers = parsers or {
        source_family: _FakeParser()
        for source_family in PRODUCTION_E2E_SOURCE_FAMILIES
    }
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=year_state,
        source_adapters=adapters,
        parser_boundaries=active_parsers,
        validation_boundary=_FakeValidationBoundary(),
        insert_repository=insert_repository or _FakeInsertRepository(),
    )
