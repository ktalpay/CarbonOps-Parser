"""Dry-run source discovery adapters for Phase 1 source families."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.source_acquisition.models import (
    SourceDiscoveryDocument,
    SourceDiscoveryResult,
    SourceDiscoveryStatus,
)
from carbonfactor_parser.source_adapters.contracts import SourceFamily


@dataclass(frozen=True)
class SourceDiscoveryDryRunAdapter:
    """Runtime-passive adapter contract for dry-run source discovery."""

    source_family: SourceFamily
    source_name: str
    source_reference: str

    def discover(self) -> SourceDiscoveryResult:
        return SourceDiscoveryResult(
            status=SourceDiscoveryStatus.DECLARED,
            documents=(
                SourceDiscoveryDocument(
                    source_family=self.source_family.value,
                    source_name=self.source_name,
                    source_reference=self.source_reference,
                    reporting_year=None,
                    status=SourceDiscoveryStatus.DECLARED,
                ),
            ),
        )


def create_phase1_source_discovery_dry_run_adapters() -> tuple[
    SourceDiscoveryDryRunAdapter,
    ...,
]:
    """Return deterministic dry-run discovery adapters for Phase 1 sources."""

    return (
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="GHG Protocol",
            source_reference="discovery://ghg_protocol/adapter",
        ),
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="DEFRA/DESNZ",
            source_reference="discovery://defra_desnz/adapter",
        ),
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.IPCC_EFDB,
            source_name="IPCC EFDB",
            source_reference="discovery://ipcc_efdb/adapter",
        ),
    )


def discover_phase1_sources_dry_run() -> tuple[SourceDiscoveryResult, ...]:
    """Return deterministic dry-run discovery results without source execution."""

    return tuple(
        adapter.discover()
        for adapter in create_phase1_source_discovery_dry_run_adapters()
    )
