"""No-op source adapter for package-level smoke tests."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceDocument,
    SourceFamily,
)


@dataclass(frozen=True)
class NoOpSourceAdapter:
    """SourceAdapter-compatible adapter that performs no source work."""

    source_family: SourceFamily = SourceFamily.GHG_PROTOCOL

    def discover(self) -> AdapterDiscoveryResult:
        return AdapterDiscoveryResult(documents=(), warnings=())

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        return AdapterParseResult(
            records=(),
            rejected_records=(),
            warnings=(),
            normalization_notes=(),
        )
