"""Intentional public exports for parser contracts and helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_PUBLIC_EXPORTS = {
    "ArtificialFixtureParser": "fixture_parser",
    "ArtificialParserAdapter": "artificial_adapter",
    "DEFRA_DESNZ_MINIMAL_CONTENT_HEADER": "defra_desnz_content_parser",
    "DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER": "defra_desnz_content_parser",
    "DefraDesnzParserAdapter": "defra_desnz_adapter",
    "DefraDesnzParser": "defra_desnz_parser",
    "ExampleInMemoryParser": "example_parser",
    "ExampleSourceSpecificParser": "example_source_specific_parser",
    "GHGProtocolParserAdapter": "ghg_protocol_adapter",
    "GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER": "ghg_protocol_content_parser",
    "IPCC_EFDB_NORMALIZED_CONTENT_HEADER": "ipcc_efdb_content_parser",
    "IpccEfdbParserAdapter": "ipcc_efdb_adapter",
    "DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES": "file_content_loader",
    "NoopParserAdapter": "noop_adapter",
    "ParserAdapter": "adapter",
    "ParserAdapterRegistry": "adapter_registry",
    "ParserExecutionIssue": "execution_result",
    "ParserExecutionIssueSeverity": "execution_result",
    "ParserExecutionPlan": "execution_plan",
    "ParserExecutionPlanStatus": "execution_plan",
    "ParserExecutionResult": "execution_result",
    "ParserExecutionResultStatus": "execution_result",
    "ParserFileContentInput": "file_content_input",
    "ParserFileContentLoadIssue": "file_content_loader",
    "ParserFileContentLoadResult": "file_content_loader",
    "ParserFileContentLoadStatus": "file_content_loader",
    "ParserFileContentValidationIssue": "file_content_input",
    "ParserFileContentValidationResult": "file_content_input",
    "ParserInputContract": "input_contract",
    "ParserInputValidationIssue": "input_contract",
    "ParserInputValidationResult": "input_contract",
    "ParserInputMapping": "input_mapping",
    "ParserInputMappingEntry": "input_mapping",
    "ParserIssue": "contracts",
    "ParserIssueSeverity": "contracts",
    "ParserPipelineSummary": "pipeline_summary",
    "ParsedRawRecord": "raw_record",
    "ParsedRawRecordPayload": "raw_record",
    "ParsedRawRecordValidationIssue": "raw_record",
    "ParsedRawRecordValidationResult": "raw_record",
    "ParserResult": "contracts",
    "ParserResultSummary": "contracts",
    "create_parser_adapter_registry": "adapter_registry",
    "create_parser_execution_result": "execution_result",
    "create_parser_file_content_input": "file_content_input",
    "create_parser_input_contract": "input_contract",
    "create_parsed_raw_record": "raw_record",
    "create_parsed_raw_record_payload": "raw_record",
    "list_parser_adapters": "adapter_registry",
    "load_parser_file_content_from_local_path": "file_content_loader",
    "plan_parser_execution": "execution_plan",
    "parse_defra_desnz_file_content": "defra_desnz_content_parser",
    "parse_ghg_protocol_file_content": "ghg_protocol_content_parser",
    "parse_ipcc_efdb_file_content": "ipcc_efdb_content_parser",
    "register_parser_adapter": "adapter_registry",
    "resolve_parser_adapters": "adapter_registry",
    "run_parser_execution": "execution_runner",
    "validate_parser_file_content_input": "file_content_input",
    "validate_parser_input_contract": "input_contract",
    "validate_parsed_raw_record": "raw_record",
    "validate_parsed_raw_record_payload": "raw_record",
    "build_fixture_parser_input_mapping": "input_mapping",
    "summarize_parser_pipeline": "pipeline_summary",
}

_PUBLIC_MODULES = (
    "adapter",
    "adapter_registry",
    "artificial_adapter",
    "contracts",
    "contract_api",
    "defra_desnz_adapter",
    "defra_desnz_content_parser",
    "defra_desnz_parser",
    "example_parser",
    "example_source_specific_parser",
    "ghg_protocol_adapter",
    "ghg_protocol_content_parser",
    "ipcc_efdb_adapter",
    "ipcc_efdb_content_parser",
    "execution_plan",
    "execution_result",
    "execution_runner",
    "file_content_input",
    "file_content_loader",
    "fixture_parser",
    "input_contract",
    "input_mapping",
    "noop_adapter",
    "pipeline_summary",
    "raw_record",
)

__all__ = tuple(_PUBLIC_EXPORTS)


def __getattr__(name: str) -> Any:
    if name in _PUBLIC_EXPORTS:
        module = import_module(f"{__name__}.{_PUBLIC_EXPORTS[name]}")
        value = getattr(module, name)
        globals()[name] = value
        return value

    if name in _PUBLIC_MODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals(), *_PUBLIC_EXPORTS, *_PUBLIC_MODULES})
