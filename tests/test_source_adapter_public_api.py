import carbonfactor_parser.source_adapters as source_adapters
from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    DefraDesnzSourceAdapter,
    ExampleSourceAdapter,
    IngestionRunStatus,
    IngestionRunSummary,
    LocalFileSourceAdapter,
    NoOpSourceAdapter,
    SourceAdapter,
    SourceAdapterExecutionResult,
    SourceAdapterResultSummary,
    SourceAdapterRegistry,
    SourceDocument,
    SourceFamily,
    build_source_document_from_file,
    create_ingestion_run_summary,
    create_source_adapter_execution_result,
    has_errors,
    has_warnings,
    sha256_hex_from_bytes,
    sha256_hex_from_file,
    sha256_hex_from_text,
    summarize_source_adapter_result,
    validate_ingestion_run_summary,
    validate_source_adapter_execution_result,
    validate_source_document_metadata,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "AdapterDiscoveryResult",
    "AdapterParseResult",
    "DefraDesnzSourceAdapter",
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


def test_expected_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "AdapterDiscoveryResult": AdapterDiscoveryResult,
        "AdapterParseResult": AdapterParseResult,
        "DefraDesnzSourceAdapter": DefraDesnzSourceAdapter,
        "ExampleSourceAdapter": ExampleSourceAdapter,
        "IngestionRunStatus": IngestionRunStatus,
        "IngestionRunSummary": IngestionRunSummary,
        "LocalFileSourceAdapter": LocalFileSourceAdapter,
        "NoOpSourceAdapter": NoOpSourceAdapter,
        "SourceAdapter": SourceAdapter,
        "SourceAdapterExecutionResult": SourceAdapterExecutionResult,
        "SourceAdapterResultSummary": SourceAdapterResultSummary,
        "SourceAdapterRegistry": SourceAdapterRegistry,
        "SourceDocument": SourceDocument,
        "SourceFamily": SourceFamily,
        "build_source_document_from_file": build_source_document_from_file,
        "create_ingestion_run_summary": create_ingestion_run_summary,
        "create_source_adapter_execution_result": create_source_adapter_execution_result,
        "has_errors": has_errors,
        "has_warnings": has_warnings,
        "sha256_hex_from_bytes": sha256_hex_from_bytes,
        "sha256_hex_from_file": sha256_hex_from_file,
        "sha256_hex_from_text": sha256_hex_from_text,
        "summarize_source_adapter_result": summarize_source_adapter_result,
        "validate_ingestion_run_summary": validate_ingestion_run_summary,
        "validate_source_adapter_execution_result": (
            validate_source_adapter_execution_result
        ),
        "validate_source_document_metadata": validate_source_document_metadata,
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(source_adapters, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_all_lists_expected_public_symbols() -> None:
    assert source_adapters.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_all_names_resolve_to_package_attributes() -> None:
    for name in source_adapters.__all__:
        assert hasattr(source_adapters, name)


def test_all_excludes_internal_and_private_names() -> None:
    excluded_names = {
        "contracts",
        "defra_desnz_adapter",
        "document_builder",
        "document_validation",
        "example_source_adapter",
        "execution_result",
        "execution_result_factory",
        "execution_result_validation",
        "hashing",
        "ingestion_run",
        "ingestion_run_factory",
        "ingestion_run_validation",
        "local_file_adapter",
        "noop_adapter",
        "registry",
        "summary",
        "_PUBLIC_EXPORTS",
    }

    assert not excluded_names.intersection(source_adapters.__all__)
    assert all(not name.startswith("_") for name in source_adapters.__all__)


def test_test_fakes_are_not_exposed_from_runtime_package() -> None:
    assert "FakeSourceAdapter" not in source_adapters.__all__
    assert not hasattr(source_adapters, "FakeSourceAdapter")
