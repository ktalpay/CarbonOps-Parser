import carbonfactor_parser.parsers as parsers
from carbonfactor_parser.parsers import (
    adapter,
    adapter_registry,
    artificial_adapter,
    contracts,
    defra_desnz_adapter,
    defra_desnz_content_parser,
    defra_desnz_parser,
    example_parser,
    example_source_specific_parser,
    ghg_protocol_adapter,
    ghg_protocol_content_parser,
    ipcc_efdb_adapter,
    ipcc_efdb_content_parser,
    execution_plan,
    execution_result,
    execution_runner,
    file_content_input,
    file_content_loader,
    fixture_parser,
    input_contract,
    input_mapping,
    noop_adapter,
    pipeline_summary,
    raw_record,
)
from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    ArtificialParserAdapter,
    DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES,
    DEFRA_DESNZ_MINIMAL_CONTENT_HEADER,
    DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER,
    DefraDesnzParserAdapter,
    DefraDesnzParser,
    ExampleInMemoryParser,
    ExampleSourceSpecificParser,
    GHGProtocolParserAdapter,
    GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER,
    IPCC_EFDB_NORMALIZED_CONTENT_HEADER,
    IpccEfdbParserAdapter,
    NoopParserAdapter,
    ParserAdapter,
    ParserAdapterRegistry,
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionPlan,
    ParserExecutionPlanStatus,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    ParserFileContentInput,
    ParserFileContentLoadIssue,
    ParserFileContentLoadResult,
    ParserFileContentLoadStatus,
    ParserFileContentValidationIssue,
    ParserFileContentValidationResult,
    ParserInputContract,
    ParserInputValidationIssue,
    ParserInputValidationResult,
    ParserInputMapping,
    ParserInputMappingEntry,
    ParserIssue,
    ParserIssueSeverity,
    ParserPipelineSummary,
    ParsedRawRecord,
    ParsedRawRecordPayload,
    ParsedRawRecordValidationIssue,
    ParsedRawRecordValidationResult,
    ParserResult,
    ParserResultSummary,
    create_parser_adapter_registry,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
    create_parser_execution_result,
    create_parser_file_content_input,
    build_fixture_parser_input_mapping,
    create_parser_input_contract,
    list_parser_adapters,
    load_parser_file_content_from_local_path,
    plan_parser_execution,
    parse_defra_desnz_file_content,
    parse_ghg_protocol_file_content,
    parse_ipcc_efdb_file_content,
    register_parser_adapter,
    resolve_parser_adapters,
    run_parser_execution,
    summarize_parser_pipeline,
    validate_parsed_raw_record,
    validate_parsed_raw_record_payload,
    validate_parser_file_content_input,
    validate_parser_input_contract,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "ArtificialFixtureParser",
    "ArtificialParserAdapter",
    "DEFRA_DESNZ_MINIMAL_CONTENT_HEADER",
    "DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER",
    "DefraDesnzParserAdapter",
    "DefraDesnzParser",
    "ExampleInMemoryParser",
    "ExampleSourceSpecificParser",
    "GHGProtocolParserAdapter",
    "GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER",
    "IPCC_EFDB_NORMALIZED_CONTENT_HEADER",
    "IpccEfdbParserAdapter",
    "DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES",
    "NoopParserAdapter",
    "ParserAdapter",
    "ParserAdapterRegistry",
    "ParserExecutionIssue",
    "ParserExecutionIssueSeverity",
    "ParserExecutionPlan",
    "ParserExecutionPlanStatus",
    "ParserExecutionResult",
    "ParserExecutionResultStatus",
    "ParserFileContentInput",
    "ParserFileContentLoadIssue",
    "ParserFileContentLoadResult",
    "ParserFileContentLoadStatus",
    "ParserFileContentValidationIssue",
    "ParserFileContentValidationResult",
    "ParserInputContract",
    "ParserInputValidationIssue",
    "ParserInputValidationResult",
    "ParserInputMapping",
    "ParserInputMappingEntry",
    "ParserIssue",
    "ParserIssueSeverity",
    "ParserPipelineSummary",
    "ParsedRawRecord",
    "ParsedRawRecordPayload",
    "ParsedRawRecordValidationIssue",
    "ParsedRawRecordValidationResult",
    "ParserResult",
    "ParserResultSummary",
    "create_parser_adapter_registry",
    "create_parser_execution_result",
    "create_parser_file_content_input",
    "create_parser_input_contract",
    "create_parsed_raw_record",
    "create_parsed_raw_record_payload",
    "list_parser_adapters",
    "load_parser_file_content_from_local_path",
    "plan_parser_execution",
    "parse_defra_desnz_file_content",
    "parse_ghg_protocol_file_content",
    "parse_ipcc_efdb_file_content",
    "register_parser_adapter",
    "resolve_parser_adapters",
    "run_parser_execution",
    "validate_parser_file_content_input",
    "validate_parser_input_contract",
    "validate_parsed_raw_record",
    "validate_parsed_raw_record_payload",
    "build_fixture_parser_input_mapping",
    "summarize_parser_pipeline",
)

EXPECTED_PUBLIC_EXPORTS = {
    "ArtificialFixtureParser": fixture_parser.ArtificialFixtureParser,
    "ArtificialParserAdapter": artificial_adapter.ArtificialParserAdapter,
    "DEFRA_DESNZ_MINIMAL_CONTENT_HEADER": (
        defra_desnz_content_parser.DEFRA_DESNZ_MINIMAL_CONTENT_HEADER
    ),
    "DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER": (
        defra_desnz_content_parser.DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER
    ),
    "DefraDesnzParserAdapter": defra_desnz_adapter.DefraDesnzParserAdapter,
    "DefraDesnzParser": defra_desnz_parser.DefraDesnzParser,
    "ExampleInMemoryParser": example_parser.ExampleInMemoryParser,
    "ExampleSourceSpecificParser": (
        example_source_specific_parser.ExampleSourceSpecificParser
    ),
    "GHGProtocolParserAdapter": ghg_protocol_adapter.GHGProtocolParserAdapter,
    "GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER": (
        ghg_protocol_content_parser.GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER
    ),
    "IPCC_EFDB_NORMALIZED_CONTENT_HEADER": (
        ipcc_efdb_content_parser.IPCC_EFDB_NORMALIZED_CONTENT_HEADER
    ),
    "IpccEfdbParserAdapter": ipcc_efdb_adapter.IpccEfdbParserAdapter,
    "DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES": (
        file_content_loader.DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES
    ),
    "NoopParserAdapter": noop_adapter.NoopParserAdapter,
    "ParserAdapter": adapter.ParserAdapter,
    "ParserAdapterRegistry": adapter_registry.ParserAdapterRegistry,
    "ParserExecutionIssue": execution_result.ParserExecutionIssue,
    "ParserExecutionIssueSeverity": (
        execution_result.ParserExecutionIssueSeverity
    ),
    "ParserExecutionPlan": execution_plan.ParserExecutionPlan,
    "ParserExecutionPlanStatus": execution_plan.ParserExecutionPlanStatus,
    "ParserExecutionResult": execution_result.ParserExecutionResult,
    "ParserExecutionResultStatus": execution_result.ParserExecutionResultStatus,
    "ParserFileContentInput": file_content_input.ParserFileContentInput,
    "ParserFileContentLoadIssue": (
        file_content_loader.ParserFileContentLoadIssue
    ),
    "ParserFileContentLoadResult": (
        file_content_loader.ParserFileContentLoadResult
    ),
    "ParserFileContentLoadStatus": (
        file_content_loader.ParserFileContentLoadStatus
    ),
    "ParserFileContentValidationIssue": (
        file_content_input.ParserFileContentValidationIssue
    ),
    "ParserFileContentValidationResult": (
        file_content_input.ParserFileContentValidationResult
    ),
    "ParserInputContract": input_contract.ParserInputContract,
    "ParserInputValidationIssue": input_contract.ParserInputValidationIssue,
    "ParserInputValidationResult": input_contract.ParserInputValidationResult,
    "ParserInputMapping": input_mapping.ParserInputMapping,
    "ParserInputMappingEntry": input_mapping.ParserInputMappingEntry,
    "ParserIssue": contracts.ParserIssue,
    "ParserIssueSeverity": contracts.ParserIssueSeverity,
    "ParserPipelineSummary": pipeline_summary.ParserPipelineSummary,
    "ParsedRawRecord": raw_record.ParsedRawRecord,
    "ParsedRawRecordPayload": raw_record.ParsedRawRecordPayload,
    "ParsedRawRecordValidationIssue": raw_record.ParsedRawRecordValidationIssue,
    "ParsedRawRecordValidationResult": (
        raw_record.ParsedRawRecordValidationResult
    ),
    "ParserResult": contracts.ParserResult,
    "ParserResultSummary": contracts.ParserResultSummary,
    "create_parser_adapter_registry": (
        adapter_registry.create_parser_adapter_registry
    ),
    "create_parser_execution_result": (
        execution_result.create_parser_execution_result
    ),
    "create_parser_file_content_input": (
        file_content_input.create_parser_file_content_input
    ),
    "create_parser_input_contract": input_contract.create_parser_input_contract,
    "create_parsed_raw_record": raw_record.create_parsed_raw_record,
    "create_parsed_raw_record_payload": (
        raw_record.create_parsed_raw_record_payload
    ),
    "list_parser_adapters": adapter_registry.list_parser_adapters,
    "load_parser_file_content_from_local_path": (
        file_content_loader.load_parser_file_content_from_local_path
    ),
    "plan_parser_execution": execution_plan.plan_parser_execution,
    "parse_defra_desnz_file_content": (
        defra_desnz_content_parser.parse_defra_desnz_file_content
    ),
    "parse_ghg_protocol_file_content": (
        ghg_protocol_content_parser.parse_ghg_protocol_file_content
    ),
    "parse_ipcc_efdb_file_content": (
        ipcc_efdb_content_parser.parse_ipcc_efdb_file_content
    ),
    "register_parser_adapter": adapter_registry.register_parser_adapter,
    "resolve_parser_adapters": adapter_registry.resolve_parser_adapters,
    "run_parser_execution": execution_runner.run_parser_execution,
    "validate_parser_file_content_input": (
        file_content_input.validate_parser_file_content_input
    ),
    "validate_parser_input_contract": input_contract.validate_parser_input_contract,
    "validate_parsed_raw_record": raw_record.validate_parsed_raw_record,
    "validate_parsed_raw_record_payload": (
        raw_record.validate_parsed_raw_record_payload
    ),
    "build_fixture_parser_input_mapping": (
        input_mapping.build_fixture_parser_input_mapping
    ),
    "summarize_parser_pipeline": pipeline_summary.summarize_parser_pipeline,
}


def test_expected_parser_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "ArtificialFixtureParser": ArtificialFixtureParser,
        "ArtificialParserAdapter": ArtificialParserAdapter,
        "DEFRA_DESNZ_MINIMAL_CONTENT_HEADER": (
            DEFRA_DESNZ_MINIMAL_CONTENT_HEADER
        ),
        "DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER": (
            DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER
        ),
        "DefraDesnzParserAdapter": DefraDesnzParserAdapter,
        "DefraDesnzParser": DefraDesnzParser,
        "ExampleInMemoryParser": ExampleInMemoryParser,
        "ExampleSourceSpecificParser": ExampleSourceSpecificParser,
        "GHGProtocolParserAdapter": GHGProtocolParserAdapter,
        "GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER": (
            GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER
        ),
        "IPCC_EFDB_NORMALIZED_CONTENT_HEADER": (
            IPCC_EFDB_NORMALIZED_CONTENT_HEADER
        ),
        "IpccEfdbParserAdapter": IpccEfdbParserAdapter,
        "DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES": (
            DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES
        ),
        "NoopParserAdapter": NoopParserAdapter,
        "ParserAdapter": ParserAdapter,
        "ParserAdapterRegistry": ParserAdapterRegistry,
        "ParserExecutionIssue": ParserExecutionIssue,
        "ParserExecutionIssueSeverity": ParserExecutionIssueSeverity,
        "ParserExecutionPlan": ParserExecutionPlan,
        "ParserExecutionPlanStatus": ParserExecutionPlanStatus,
        "ParserExecutionResult": ParserExecutionResult,
        "ParserExecutionResultStatus": ParserExecutionResultStatus,
        "ParserFileContentInput": ParserFileContentInput,
        "ParserFileContentLoadIssue": ParserFileContentLoadIssue,
        "ParserFileContentLoadResult": ParserFileContentLoadResult,
        "ParserFileContentLoadStatus": ParserFileContentLoadStatus,
        "ParserFileContentValidationIssue": ParserFileContentValidationIssue,
        "ParserFileContentValidationResult": ParserFileContentValidationResult,
        "ParserInputContract": ParserInputContract,
        "ParserInputValidationIssue": ParserInputValidationIssue,
        "ParserInputValidationResult": ParserInputValidationResult,
        "ParserInputMapping": ParserInputMapping,
        "ParserInputMappingEntry": ParserInputMappingEntry,
        "ParserIssue": ParserIssue,
        "ParserIssueSeverity": ParserIssueSeverity,
        "ParserPipelineSummary": ParserPipelineSummary,
        "ParsedRawRecord": ParsedRawRecord,
        "ParsedRawRecordPayload": ParsedRawRecordPayload,
        "ParsedRawRecordValidationIssue": ParsedRawRecordValidationIssue,
        "ParsedRawRecordValidationResult": ParsedRawRecordValidationResult,
        "ParserResult": ParserResult,
        "ParserResultSummary": ParserResultSummary,
        "create_parser_adapter_registry": create_parser_adapter_registry,
        "create_parser_execution_result": create_parser_execution_result,
        "create_parser_file_content_input": create_parser_file_content_input,
        "create_parser_input_contract": create_parser_input_contract,
        "create_parsed_raw_record": create_parsed_raw_record,
        "create_parsed_raw_record_payload": create_parsed_raw_record_payload,
        "list_parser_adapters": list_parser_adapters,
        "load_parser_file_content_from_local_path": (
            load_parser_file_content_from_local_path
        ),
        "plan_parser_execution": plan_parser_execution,
        "parse_defra_desnz_file_content": parse_defra_desnz_file_content,
        "parse_ghg_protocol_file_content": parse_ghg_protocol_file_content,
        "parse_ipcc_efdb_file_content": parse_ipcc_efdb_file_content,
        "register_parser_adapter": register_parser_adapter,
        "resolve_parser_adapters": resolve_parser_adapters,
        "run_parser_execution": run_parser_execution,
        "validate_parser_file_content_input": validate_parser_file_content_input,
        "validate_parser_input_contract": validate_parser_input_contract,
        "validate_parsed_raw_record": validate_parsed_raw_record,
        "validate_parsed_raw_record_payload": validate_parsed_raw_record_payload,
        "build_fixture_parser_input_mapping": build_fixture_parser_input_mapping,
        "summarize_parser_pipeline": summarize_parser_pipeline,
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(parsers, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_parser_all_lists_expected_public_symbols() -> None:
    assert parsers.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_parser_public_exports_match_origin_modules() -> None:
    assert {
        name: getattr(parsers, name) for name in EXPECTED_PUBLIC_SYMBOLS
    } == EXPECTED_PUBLIC_EXPORTS


def test_parser_all_names_resolve_to_package_attributes() -> None:
    for name in parsers.__all__:
        assert hasattr(parsers, name)


def test_parser_all_excludes_internal_module_names() -> None:
    assert "adapter" not in parsers.__all__
    assert "adapter_registry" not in parsers.__all__
    assert "artificial_adapter" not in parsers.__all__
    assert "contracts" not in parsers.__all__
    assert "defra_desnz_adapter" not in parsers.__all__
    assert "defra_desnz_content_parser" not in parsers.__all__
    assert "defra_desnz_parser" not in parsers.__all__
    assert "example_parser" not in parsers.__all__
    assert "example_source_specific_parser" not in parsers.__all__
    assert "execution_plan" not in parsers.__all__
    assert "execution_result" not in parsers.__all__
    assert "execution_runner" not in parsers.__all__
    assert "file_content_input" not in parsers.__all__
    assert "file_content_loader" not in parsers.__all__
    assert "fixture_parser" not in parsers.__all__
    assert "input_contract" not in parsers.__all__
    assert "input_mapping" not in parsers.__all__
    assert "ipcc_efdb_adapter" not in parsers.__all__
    assert "ipcc_efdb_content_parser" not in parsers.__all__
    assert "noop_adapter" not in parsers.__all__
    assert "pipeline_summary" not in parsers.__all__
    assert "raw_record" not in parsers.__all__
    assert all(not name.startswith("_") for name in parsers.__all__)
