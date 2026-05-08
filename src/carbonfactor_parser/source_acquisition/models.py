"""Source acquisition configuration models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceDiscoveryStatus(str, Enum):
    """Runtime-passive source discovery contract status values."""

    DECLARED = "declared"


class SourceAcquisitionPlanMode(str, Enum):
    """Runtime-passive source acquisition planning modes."""

    DRY_RUN = "dry_run"


class SourceAcquisitionDryRunResultStatus(str, Enum):
    """Runtime-passive source acquisition dry-run result statuses."""

    PLANNED = "planned"


@dataclass(frozen=True)
class SourceAcquisitionDescriptor:
    """Immutable metadata describing a known source acquisition family."""

    source_id: str
    source_family: str
    display_name: str
    homepage_url: str
    acquisition_url: str
    expected_format: str
    description: str
    enabled: bool = True


@dataclass(frozen=True)
class SourceDiscoveryDocument:
    """Dry-run discovery metadata for a Phase 1 source document reference."""

    source_family: str
    source_name: str
    source_reference: str
    reporting_year: int | None = None
    status: SourceDiscoveryStatus = SourceDiscoveryStatus.DECLARED


@dataclass(frozen=True)
class SourceDiscoveryResult:
    """Deterministic collection of dry-run source discovery metadata."""

    status: SourceDiscoveryStatus
    documents: tuple[SourceDiscoveryDocument, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceAcquisitionRequest:
    """Runtime-passive request for a Phase 1 source acquisition plan."""

    selected_source_families: tuple[str, ...]
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class SourceAcquisitionPlan:
    """Runtime-passive Phase 1 source acquisition plan."""

    mode: SourceAcquisitionPlanMode
    selected_source_families: tuple[str, ...]
    discovery_results: tuple[SourceDiscoveryResult, ...]


@dataclass(frozen=True)
class SourceAcquisitionDryRunFamilyResult:
    """Runtime-passive dry-run result summary for one source family."""

    source_family: str
    status: SourceAcquisitionDryRunResultStatus
    planned_document_count: int
    discovery_result: SourceDiscoveryResult
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceAcquisitionDryRunExecutionResult:
    """Runtime-passive result of evaluating a source acquisition plan."""

    status: SourceAcquisitionDryRunResultStatus
    mode: SourceAcquisitionPlanMode
    selected_source_families: tuple[str, ...]
    family_results: tuple[SourceAcquisitionDryRunFamilyResult, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceDownloadRequest:
    """Runtime-passive request describing a future source download."""

    source_family: str
    source_name: str
    source_reference: str
    target_logical_path: str
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class SourceDownloadBatchPlan:
    """Runtime-passive batch of source download requests."""

    mode: SourceAcquisitionPlanMode
    selected_source_families: tuple[str, ...]
    requests: tuple[SourceDownloadRequest, ...]
