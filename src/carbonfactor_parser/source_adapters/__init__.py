"""Conceptual source adapter contracts."""

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapter,
    SourceDocument,
    SourceFamily,
)
from carbonfactor_parser.source_adapters.document_builder import (
    build_source_document_from_file,
)
from carbonfactor_parser.source_adapters.document_validation import (
    validate_source_document_metadata,
)
from carbonfactor_parser.source_adapters.hashing import (
    sha256_hex_from_bytes,
    sha256_hex_from_file,
    sha256_hex_from_text,
)
from carbonfactor_parser.source_adapters.ingestion_run import (
    IngestionRunStatus,
    IngestionRunSummary,
)
from carbonfactor_parser.source_adapters.ingestion_run_validation import (
    validate_ingestion_run_summary,
)
from carbonfactor_parser.source_adapters.registry import SourceAdapterRegistry

__all__ = [
    "AdapterDiscoveryResult",
    "AdapterParseResult",
    "IngestionRunStatus",
    "IngestionRunSummary",
    "SourceAdapter",
    "SourceAdapterRegistry",
    "SourceDocument",
    "SourceFamily",
    "build_source_document_from_file",
    "sha256_hex_from_bytes",
    "sha256_hex_from_file",
    "sha256_hex_from_text",
    "validate_ingestion_run_summary",
    "validate_source_document_metadata",
]
