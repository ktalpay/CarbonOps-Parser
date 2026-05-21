"""Production E2E year-based orchestration boundary.

This module coordinates injected runtime boundaries only. It does not implement
live source integrations, credentials, scheduling, or source-specific parsers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re
from typing import Mapping, Protocol, Sequence, runtime_checkable

from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputBatch,
)
from carbonfactor_parser.persistence.postgresql_runtime_config import (
    POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
)


PRODUCTION_E2E_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

_SOURCE_FAMILY_ALIASES: Mapping[str, str] = {
    "ghg": "ghg_protocol",
    "ghg_protocol": "ghg_protocol",
    "defra": "defra_desnz",
    "desnz": "defra_desnz",
    "defra_desnz": "defra_desnz",
    "ipcc": "ipcc_efdb",
    "ipcc_efdb": "ipcc_efdb",
}

_YEAR_STATE_KEYS: Mapping[str, str] = {
    "ghg_protocol": "ghg",
    "defra_desnz": "defra",
    "ipcc_efdb": "ipcc",
}


class ProductionE2EYearRunStatus(str, Enum):
    """Top-level production E2E year orchestrator statuses."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    FAILED = "failed"


class ProductionE2EYearFamilyStatus(str, Enum):
    """Per-source-family production E2E year statuses."""

    COMPLETED = "completed"
    NO_AVAILABLE_SOURCE_YEAR = "no_available_source_year"
    FAILED = "failed"


class ProductionE2EYearSelectionStatus(str, Enum):
    """Year-state selection statuses."""

    INITIAL_YEAR_SELECTED = "initial_year_selected"
    NEXT_YEAR_SELECTED = "next_year_selected"


class ProductionE2ESourceYearDiscoveryStatus(str, Enum):
    """Target-year source discovery statuses."""

    SOURCE_YEAR_AVAILABLE = "source_year_available"
    NO_AVAILABLE_SOURCE_YEAR = "no_available_source_year"


class ProductionE2ESourceYearDownloadStatus(str, Enum):
    """Target-year download statuses."""

    DOWNLOADED = "downloaded"
    FAILED = "failed"


class ProductionE2EValidationStatus(str, Enum):
    """Validation statuses for parsed normalized output."""

    VALIDATED = "validated"
    FAILED_VALIDATION = "failed_validation"


@dataclass(frozen=True)
class ProductionE2EFailureDetail:
    """Structured failure detail emitted by the orchestrator."""

    source_family: str | None
    stage: str
    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class ProductionE2EYearState:
    """Selected target year for one source family."""

    source_family: str
    year_state_key: str
    latest_year: int | None
    target_year: int
    initial_year: int
    selection_status: ProductionE2EYearSelectionStatus


@dataclass(frozen=True)
class ProductionE2ESourceYearDiscoveryRequest:
    """Request sent to a source-family adapter for one target year."""

    source_family: str
    target_year: int
    run_id: str
    correlation_id: str | None = None


@dataclass(frozen=True)
class ProductionE2ESourceYearDiscoveryResult:
    """Source-family target-year discovery result."""

    status: ProductionE2ESourceYearDiscoveryStatus
    source_family: str
    target_year: int
    artifact_reference: str | None = None
    reason_code: str | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ProductionE2EDownloadedArtifact:
    """Downloaded or local source artifact returned by a source adapter."""

    source_family: str
    source_year: int
    artifact_reference: str
    checksum_sha256: str | None = None
    content_type: str | None = None
    format_hint: str | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ProductionE2ESourceYearDownloadResult:
    """Source-family target-year download result."""

    status: ProductionE2ESourceYearDownloadStatus
    source_family: str
    target_year: int
    artifact: ProductionE2EDownloadedArtifact | None = None
    issues: tuple[ProductionE2EFailureDetail, ...] = ()


@dataclass(frozen=True)
class ProductionE2EValidationResult:
    """Validation result for parsed normalized output before insert."""

    status: ProductionE2EValidationStatus
    diagnostic_count: int = 0
    blocking_error_count: int = 0
    warning_count: int = 0
    issues: tuple[ProductionE2EFailureDetail, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return whether the validation result permits persistence."""

        return (
            self.status is ProductionE2EValidationStatus.VALIDATED
            and self.blocking_error_count == 0
        )


@dataclass(frozen=True)
class ProductionE2EInsertSummary:
    """Repository insert summary consumed by the orchestrator."""

    status: str
    attempted: int
    inserted: int
    skipped_duplicate: int = 0
    failed: int = 0
    validation_error_count: int = 0
    master_inserted: int = 0
    master_skipped: int = 0
    detail_inserted: int = 0
    detail_skipped: int = 0

    @property
    def is_success(self) -> bool:
        """Return whether the insert summary has no failed rows."""

        return self.failed == 0 and not self.status.startswith("failed")


@dataclass(frozen=True)
class ProductionE2EYearFamilyResult:
    """Structured run summary for one source family."""

    source_family: str
    status: ProductionE2EYearFamilyStatus
    year_state: ProductionE2EYearState
    discovery_result: ProductionE2ESourceYearDiscoveryResult | None = None
    download_result: ProductionE2ESourceYearDownloadResult | None = None
    parsed_row_count: int = 0
    validation_result: ProductionE2EValidationResult | None = None
    insert_summary: ProductionE2EInsertSummary | None = None
    recorded_ingested_year: int | None = None
    failures: tuple[ProductionE2EFailureDetail, ...] = ()


@dataclass(frozen=True)
class ProductionE2EYearRunSummary:
    """Aggregated production E2E year run summary."""

    requested_family_count: int
    completed_family_count: int
    no_available_source_year_count: int
    failed_family_count: int
    parsed_row_count: int
    attempted_insert_count: int
    inserted_count: int
    skipped_duplicate_count: int
    failed_insert_count: int
    failure_count: int


@dataclass(frozen=True)
class ProductionE2EYearOrchestratorRequest:
    """Request for a single production E2E year-based run."""

    run_id: str
    enabled_source_families: tuple[str, ...] = PRODUCTION_E2E_SOURCE_FAMILIES
    initial_year: int = POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR
    correlation_id: str | None = None


@dataclass(frozen=True)
class ProductionE2EYearOrchestratorResult:
    """Top-level production E2E year orchestration result."""

    status: ProductionE2EYearRunStatus
    request: ProductionE2EYearOrchestratorRequest
    selected_source_families: tuple[str, ...]
    family_results: tuple[ProductionE2EYearFamilyResult, ...]
    summary: ProductionE2EYearRunSummary
    failures: tuple[ProductionE2EFailureDetail, ...] = ()


@runtime_checkable
class ProductionE2EYearStateRepository(Protocol):
    """Repository boundary for PostgreSQL source-family year state."""

    def latest_ingested_year(self, source_family: str) -> int | None:
        """Return the latest ingested year for a source-family year-state key."""

    def record_ingested_year(self, source_family: str, ingested_year: int) -> None:
        """Record a successfully ingested source-family year."""


@runtime_checkable
class ProductionE2ESourceFamilyAdapter(Protocol):
    """Source-family adapter boundary for target-year discovery and download."""

    @property
    def source_family(self) -> str:
        """Return the canonical source family handled by this adapter."""

    def discover_target_year(
        self,
        request: ProductionE2ESourceYearDiscoveryRequest,
    ) -> ProductionE2ESourceYearDiscoveryResult:
        """Discover availability for exactly one target year."""

    def download_target_year(
        self,
        discovery_result: ProductionE2ESourceYearDiscoveryResult,
    ) -> ProductionE2ESourceYearDownloadResult:
        """Download or locate the artifact for a discovered target year."""


@runtime_checkable
class ProductionE2EParserBoundary(Protocol):
    """Parser boundary for a downloaded/local source artifact."""

    def parse(
        self,
        artifact: ProductionE2EDownloadedArtifact,
    ) -> ParserNormalizedOutputBatch:
        """Parse the downloaded/local artifact into normalized output rows."""


@runtime_checkable
class ProductionE2EValidationBoundary(Protocol):
    """Validation boundary for parsed normalized output."""

    def validate(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> ProductionE2EValidationResult:
        """Validate normalized output before persistence."""


@runtime_checkable
class ProductionE2EInsertRepository(Protocol):
    """PostgreSQL insert repository boundary for normalized output."""

    def insert_normalized_factor_records(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> object:
        """Insert normalized output into PostgreSQL."""


@dataclass(frozen=True)
class ProductionE2EYearOrchestratorDependencies:
    """Injected dependencies for the production E2E year orchestrator."""

    year_state_repository: ProductionE2EYearStateRepository
    source_adapters: Mapping[str, ProductionE2ESourceFamilyAdapter]
    parser_boundaries: Mapping[str, ProductionE2EParserBoundary]
    validation_boundary: ProductionE2EValidationBoundary
    insert_repository: ProductionE2EInsertRepository


def run_production_e2e_year_orchestrator(
    request: ProductionE2EYearOrchestratorRequest,
    dependencies: ProductionE2EYearOrchestratorDependencies,
) -> ProductionE2EYearOrchestratorResult:
    """Run the production E2E year-based boundary with injected adapters."""

    if request.initial_year < 1:
        raise ValueError("initial_year must be positive.")

    selected_families, selection_failures = _normalize_source_families(
        request.enabled_source_families,
    )
    family_results = [
        _failed_family_without_runtime(
            source_family=source_family,
            request=request,
            failure=failure,
            latest_year=None,
        )
        for source_family, failure in selection_failures
    ]

    for source_family in selected_families:
        family_results.append(
            _run_source_family(
                source_family=source_family,
                request=request,
                dependencies=dependencies,
            ),
        )

    summary = _summarize(request.enabled_source_families, family_results)
    failures = tuple(
        failure
        for family_result in family_results
        for failure in family_result.failures
    )
    if summary.failed_family_count:
        status = (
            ProductionE2EYearRunStatus.FAILED
            if summary.completed_family_count == 0
            and summary.no_available_source_year_count == 0
            else ProductionE2EYearRunStatus.COMPLETED_WITH_FAILURES
        )
    else:
        status = ProductionE2EYearRunStatus.COMPLETED

    return ProductionE2EYearOrchestratorResult(
        status=status,
        request=request,
        selected_source_families=selected_families,
        family_results=tuple(family_results),
        summary=summary,
        failures=failures,
    )


def _run_source_family(
    *,
    source_family: str,
    request: ProductionE2EYearOrchestratorRequest,
    dependencies: ProductionE2EYearOrchestratorDependencies,
) -> ProductionE2EYearFamilyResult:
    latest_year = dependencies.year_state_repository.latest_ingested_year(
        _YEAR_STATE_KEYS[source_family],
    )
    year_state = _select_year_state(source_family, latest_year, request.initial_year)

    adapter = dependencies.source_adapters.get(source_family)
    if adapter is None:
        return _failed_family(
            year_state,
            _failure(
                source_family,
                "source_adapter",
                "PRODUCTION_E2E_MISSING_SOURCE_ADAPTER",
                "No source-family adapter is configured.",
                "dependencies.source_adapters",
            ),
        )

    parser = dependencies.parser_boundaries.get(source_family)
    if parser is None:
        return _failed_family(
            year_state,
            _failure(
                source_family,
                "parser",
                "PRODUCTION_E2E_MISSING_PARSER_BOUNDARY",
                "No parser boundary is configured.",
                "dependencies.parser_boundaries",
            ),
        )

    discovery_result = adapter.discover_target_year(
        ProductionE2ESourceYearDiscoveryRequest(
            source_family=source_family,
            target_year=year_state.target_year,
            run_id=request.run_id,
            correlation_id=request.correlation_id,
        ),
    )
    if (
        discovery_result.status
        is ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR
    ):
        return ProductionE2EYearFamilyResult(
            source_family=source_family,
            status=ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR,
            year_state=year_state,
            discovery_result=discovery_result,
        )
    if (
        discovery_result.status
        is not ProductionE2ESourceYearDiscoveryStatus.SOURCE_YEAR_AVAILABLE
    ):
        return _failed_family(
            year_state,
            _failure(
                source_family,
                "discovery",
                "PRODUCTION_E2E_SOURCE_DISCOVERY_FAILED",
                "Source-family discovery did not return an available target year.",
                "discovery_result.status",
            ),
            discovery_result=discovery_result,
        )

    download_result = adapter.download_target_year(discovery_result)
    if (
        download_result.status is not ProductionE2ESourceYearDownloadStatus.DOWNLOADED
        or download_result.artifact is None
    ):
        failures = download_result.issues or (
            _failure(
                source_family,
                "download",
                "PRODUCTION_E2E_SOURCE_DOWNLOAD_FAILED",
                "Source-family download did not return an artifact.",
                "download_result.artifact",
            ),
        )
        return _failed_family(
            year_state,
            *failures,
            discovery_result=discovery_result,
            download_result=download_result,
        )

    try:
        batch = parser.parse(download_result.artifact)
    except Exception as exc:  # noqa: BLE001 - parser boundaries vary by source
        return _failed_family(
            year_state,
            _failure(
                source_family,
                "parser",
                "PRODUCTION_E2E_PARSER_FAILED",
                _redact_sensitive_text(str(exc) or exc.__class__.__name__),
                "parser",
            ),
            discovery_result=discovery_result,
            download_result=download_result,
        )
    validation_result = dependencies.validation_boundary.validate(batch)
    if not validation_result.is_valid:
        failures = validation_result.issues or (
            _failure(
                source_family,
                "validation",
                "PRODUCTION_E2E_VALIDATION_FAILED",
                "Parsed normalized output failed validation.",
                "validation_result.status",
            ),
        )
        return _failed_family(
            year_state,
            *failures,
            discovery_result=discovery_result,
            download_result=download_result,
            parsed_row_count=batch.row_count,
            validation_result=validation_result,
        )

    insert_batch = _batch_with_run_id(batch, request.run_id)
    insert_summary = _coerce_insert_summary(
        dependencies.insert_repository.insert_normalized_factor_records(insert_batch),
    )
    if not insert_summary.is_success:
        return _failed_family(
            year_state,
            _failure(
                source_family,
                "insert",
                "PRODUCTION_E2E_POSTGRESQL_INSERT_FAILED",
                "PostgreSQL insert repository returned a failed summary.",
                "insert_summary.status",
            ),
            discovery_result=discovery_result,
            download_result=download_result,
            parsed_row_count=batch.row_count,
            validation_result=validation_result,
            insert_summary=insert_summary,
        )

    dependencies.year_state_repository.record_ingested_year(
        _YEAR_STATE_KEYS[source_family],
        year_state.target_year,
    )
    return ProductionE2EYearFamilyResult(
        source_family=source_family,
        status=ProductionE2EYearFamilyStatus.COMPLETED,
        year_state=year_state,
        discovery_result=discovery_result,
        download_result=download_result,
        parsed_row_count=batch.row_count,
        validation_result=validation_result,
        insert_summary=insert_summary,
        recorded_ingested_year=year_state.target_year,
    )


def _normalize_source_families(
    source_families: Sequence[str],
) -> tuple[tuple[str, ...], tuple[tuple[str, ProductionE2EFailureDetail], ...]]:
    selected: list[str] = []
    failures: list[tuple[str, ProductionE2EFailureDetail]] = []
    for source_family in source_families:
        normalized = _SOURCE_FAMILY_ALIASES.get(source_family)
        if normalized is None:
            failures.append(
                (
                    source_family,
                    _failure(
                        source_family,
                        "selection",
                        "PRODUCTION_E2E_UNKNOWN_SOURCE_FAMILY",
                        "Enabled source family is not supported by this boundary.",
                        "request.enabled_source_families",
                    ),
                )
            )
            continue
        if normalized not in selected:
            selected.append(normalized)
    return tuple(selected), tuple(failures)


def _select_year_state(
    source_family: str,
    latest_year: int | None,
    initial_year: int,
) -> ProductionE2EYearState:
    return ProductionE2EYearState(
        source_family=source_family,
        year_state_key=_YEAR_STATE_KEYS[source_family],
        latest_year=latest_year,
        target_year=initial_year if latest_year is None else latest_year + 1,
        initial_year=initial_year,
        selection_status=(
            ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED
            if latest_year is None
            else ProductionE2EYearSelectionStatus.NEXT_YEAR_SELECTED
        ),
    )


def _coerce_insert_summary(result: object) -> ProductionE2EInsertSummary:
    return ProductionE2EInsertSummary(
        status=_status_value(getattr(result, "status")),
        attempted=int(getattr(result, "attempted")),
        inserted=int(getattr(result, "inserted")),
        skipped_duplicate=int(getattr(result, "skipped_duplicate", 0)),
        failed=int(getattr(result, "failed", 0)),
        validation_error_count=int(getattr(result, "validation_error_count", 0)),
        master_inserted=int(getattr(result, "master_inserted", 0)),
        master_skipped=int(getattr(result, "master_skipped", 0)),
        detail_inserted=int(getattr(result, "detail_inserted", 0)),
        detail_skipped=int(getattr(result, "detail_skipped", 0)),
    )


def _batch_with_run_id(
    batch: ParserNormalizedOutputBatch,
    run_id: str,
) -> ParserNormalizedOutputBatch:
    rows = []
    for row in batch.rows:
        fields = dict(row.normalized_fields)
        fields.setdefault("run_id", run_id)
        rows.append(
            replace(
                row,
                normalized_fields=tuple(
                    sorted(fields.items(), key=lambda item: item[0])
                ),
            )
        )
    return ParserNormalizedOutputBatch(rows=tuple(rows))


def _status_value(status: object) -> str:
    value = getattr(status, "value", status)
    return str(value)


def _redact_sensitive_text(value: str) -> str:
    redacted = re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", value)
    redacted = re.sub(r"(://)[^/@\s]+@([^/\s]+)", r"\1***@\2", redacted)
    redacted = re.sub(
        r"(?i)(api[_-]?key|authorization|credential|password|passwd|pwd|"
        r"token|secret|key|access[_-]?key|private[_-]?key)=([^&\s]+)",
        r"\1=***",
        redacted,
    )
    return redacted


def _summarize(
    requested_source_families: Sequence[str],
    family_results: Sequence[ProductionE2EYearFamilyResult],
) -> ProductionE2EYearRunSummary:
    return ProductionE2EYearRunSummary(
        requested_family_count=len(requested_source_families),
        completed_family_count=sum(
            result.status is ProductionE2EYearFamilyStatus.COMPLETED
            for result in family_results
        ),
        no_available_source_year_count=sum(
            result.status is ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR
            for result in family_results
        ),
        failed_family_count=sum(
            result.status is ProductionE2EYearFamilyStatus.FAILED
            for result in family_results
        ),
        parsed_row_count=sum(result.parsed_row_count for result in family_results),
        attempted_insert_count=sum(
            result.insert_summary.attempted
            for result in family_results
            if result.insert_summary is not None
        ),
        inserted_count=sum(
            result.insert_summary.inserted
            for result in family_results
            if result.insert_summary is not None
        ),
        skipped_duplicate_count=sum(
            result.insert_summary.skipped_duplicate
            for result in family_results
            if result.insert_summary is not None
        ),
        failed_insert_count=sum(
            result.insert_summary.failed
            for result in family_results
            if result.insert_summary is not None
        ),
        failure_count=sum(len(result.failures) for result in family_results),
    )


def _failed_family_without_runtime(
    *,
    source_family: str,
    request: ProductionE2EYearOrchestratorRequest,
    failure: ProductionE2EFailureDetail,
    latest_year: int | None,
) -> ProductionE2EYearFamilyResult:
    canonical = _SOURCE_FAMILY_ALIASES.get(source_family, source_family)
    year_state_key = _YEAR_STATE_KEYS.get(canonical, source_family)
    year_state = ProductionE2EYearState(
        source_family=canonical,
        year_state_key=year_state_key,
        latest_year=latest_year,
        target_year=request.initial_year if latest_year is None else latest_year + 1,
        initial_year=request.initial_year,
        selection_status=(
            ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED
            if latest_year is None
            else ProductionE2EYearSelectionStatus.NEXT_YEAR_SELECTED
        ),
    )
    return _failed_family(year_state, failure)


def _failed_family(
    year_state: ProductionE2EYearState,
    *failures: ProductionE2EFailureDetail,
    discovery_result: ProductionE2ESourceYearDiscoveryResult | None = None,
    download_result: ProductionE2ESourceYearDownloadResult | None = None,
    parsed_row_count: int = 0,
    validation_result: ProductionE2EValidationResult | None = None,
    insert_summary: ProductionE2EInsertSummary | None = None,
) -> ProductionE2EYearFamilyResult:
    return ProductionE2EYearFamilyResult(
        source_family=year_state.source_family,
        status=ProductionE2EYearFamilyStatus.FAILED,
        year_state=year_state,
        discovery_result=discovery_result,
        download_result=download_result,
        parsed_row_count=parsed_row_count,
        validation_result=validation_result,
        insert_summary=insert_summary,
        failures=tuple(failures),
    )


def _failure(
    source_family: str | None,
    stage: str,
    code: str,
    message: str,
    field_name: str | None = None,
) -> ProductionE2EFailureDetail:
    return ProductionE2EFailureDetail(
        source_family=source_family,
        stage=stage,
        code=code,
        message=message,
        field_name=field_name,
    )
