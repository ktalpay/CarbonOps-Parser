"""Intentional public exports for source adapter contracts and helpers."""

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
from carbonfactor_parser.source_adapters.example_source_adapter import (
    ExampleSourceAdapter,
)
from carbonfactor_parser.source_adapters.execution_result import (
    SourceAdapterExecutionResult,
    has_errors,
    has_warnings,
)
from carbonfactor_parser.source_adapters.execution_result_factory import (
    create_source_adapter_execution_result,
)
from carbonfactor_parser.source_adapters.execution_result_validation import (
    validate_source_adapter_execution_result,
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
from carbonfactor_parser.source_adapters.ingestion_run_factory import (
    create_ingestion_run_summary,
)
from carbonfactor_parser.source_adapters.ingestion_run_validation import (
    validate_ingestion_run_summary,
)
from carbonfactor_parser.source_adapters.local_file_adapter import LocalFileSourceAdapter
from carbonfactor_parser.source_adapters.noop_adapter import NoOpSourceAdapter
from carbonfactor_parser.source_adapters.registry import SourceAdapterRegistry
from carbonfactor_parser.source_adapters.summary import (
    SourceAdapterResultSummary,
    summarize_source_adapter_result,
)

__all__ = (
    "AdapterDiscoveryResult",
    "AdapterParseResult",
    "ExampleSourceAdapter",
    "IngestionRunStatus",
    "IngestionRunSummary",
    "LocalFileSourceAdapter",
    "NoOpSourceAdapter",
    "SourceAdapter",
    "SourceAdapterExecutionResult",
    "SourceAdapterResultSummary",
    "SourceAdapterRegistry",
    "SourceDocument",
    "SourceFamily",
    "build_source_document_from_file",
    "create_ingestion_run_summary",
    "create_source_adapter_execution_result",
    "has_errors",
    "has_warnings",
    "sha256_hex_from_bytes",
    "sha256_hex_from_file",
    "sha256_hex_from_text",
    "summarize_source_adapter_result",
    "validate_ingestion_run_summary",
    "validate_source_adapter_execution_result",
    "validate_source_document_metadata",
)
