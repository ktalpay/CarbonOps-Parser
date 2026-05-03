"""Conceptual source adapter contracts."""

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapter,
    SourceDocument,
    SourceFamily,
)
from carbonfactor_parser.source_adapters.registry import SourceAdapterRegistry

__all__ = [
    "AdapterDiscoveryResult",
    "AdapterParseResult",
    "SourceAdapter",
    "SourceAdapterRegistry",
    "SourceDocument",
    "SourceFamily",
]
