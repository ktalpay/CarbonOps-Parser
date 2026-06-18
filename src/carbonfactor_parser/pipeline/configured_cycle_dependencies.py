"""Configured cycle dependency composition.

This module wires configured-cycle runtime dependencies for the production
E2E year orchestrator without owning the runner loop, startup summary, cycle
summary output, or run-history persistence behavior.
"""

from __future__ import annotations

from typing import Mapping

from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupResult,
)
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
)
from carbonfactor_parser.pipeline.configured_cycle_config import (
    ConfiguredCycleRunnerConfig,
    ConfiguredSourceYearArtifact,
)
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzPhase2ValidationBoundary,
    DefraDesnzProductionParserBoundary,
    DefraDesnzProductionSourceAdapter,
    DefraDesnzSourceYear,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
    GHGProtocolPhase2ValidationBoundary,
    GHGProtocolProductionParserBoundary,
    GHGProtocolProductionSourceAdapter,
    GHGProtocolSourceYear,
)
from carbonfactor_parser.pipeline.ipcc_efdb_production_e2e import (
    IPCC_EFDB_SOURCE_FAMILY,
    IpccEfdbPhase2ValidationBoundary,
    IpccEfdbProductionParserBoundary,
    IpccEfdbProductionSourceAdapter,
    IpccEfdbSourceYear,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EValidationResult,
    ProductionE2EYearOrchestratorDependencies,
)
from carbonfactor_parser.pipeline.source_artifact_transport import (
    build_configured_artifact_transport,
)


class ConfiguredCycleValidationBoundary:
    """Route validation to the source-family-specific validation boundary."""

    def __init__(self) -> None:
        self._boundaries = {
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolPhase2ValidationBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzPhase2ValidationBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbPhase2ValidationBoundary(),
        }

    def validate(self, batch: object) -> ProductionE2EValidationResult:
        rows = tuple(getattr(batch, "rows", ()))
        source_family = rows[0].source_family if rows else GHG_PROTOCOL_SOURCE_FAMILY
        boundary = self._boundaries.get(source_family)
        if boundary is None:
            boundary = GHGProtocolPhase2ValidationBoundary()
        return boundary.validate(batch)


def build_configured_cycle_dependencies(
    config: ConfiguredCycleRunnerConfig,
    runtime: PostgreSQLRuntimeStartupResult,
) -> ProductionE2EYearOrchestratorDependencies:
    """Build production E2E dependencies for the configured cycle runner."""

    transport = build_configured_artifact_transport(
        allow_live_source_access=config.allow_live_source_access,
    )
    source_years = config.source_years or {}
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=runtime.year_state_repository,
        source_adapters={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ghg_source_years(
                    source_years.get(GHG_PROTOCOL_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_defra_source_years(
                    source_years.get(DEFRA_DESNZ_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ipcc_source_years(
                    source_years.get(IPCC_EFDB_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
        },
        parser_boundaries={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionParserBoundary(),
        },
        validation_boundary=ConfiguredCycleValidationBoundary(),
        insert_repository=PostgreSQLSourceFamilyRuntimeRepository(runtime.connection),
    )


def _ghg_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, GHGProtocolSourceYear]:
    return {
        year: GHGProtocolSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _defra_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, DefraDesnzSourceYear]:
    return {
        year: DefraDesnzSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _ipcc_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, IpccEfdbSourceYear]:
    return {
        year: IpccEfdbSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


__all__ = (
    "ConfiguredCycleValidationBoundary",
    "build_configured_cycle_dependencies",
)
