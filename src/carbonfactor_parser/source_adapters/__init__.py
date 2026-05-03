"""Conceptual source adapter contracts."""

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapter,
    SourceDocument,
    SourceFamily,
)
from carbonfactor_parser.source_adapters.hashing import (
    sha256_hex_from_bytes,
    sha256_hex_from_file,
    sha256_hex_from_text,
)
from carbonfactor_parser.source_adapters.registry import SourceAdapterRegistry

__all__ = [
    "AdapterDiscoveryResult",
    "AdapterParseResult",
    "SourceAdapter",
    "SourceAdapterRegistry",
    "SourceDocument",
    "SourceFamily",
    "sha256_hex_from_bytes",
    "sha256_hex_from_file",
    "sha256_hex_from_text",
]
