import carbonfactor_parser.parsers as parsers
from carbonfactor_parser.parsers import (
    adapter,
    adapter_registry,
    contracts,
    defra_desnz_parser,
    example_parser,
    example_source_specific_parser,
    execution_plan,
    fixture_parser,
    input_contract,
    input_mapping,
    pipeline_summary,
)
from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    DefraDesnzParser,
    ExampleInMemoryParser,
    ExampleSourceSpecificParser,
    ParserAdapter,
    ParserAdapterRegistry,
    ParserExecutionPlan,
    ParserExecutionPlanStatus,
    ParserInputContract,
    ParserInputValidationIssue,
    ParserInputValidationResult,
    ParserInputMapping,
    ParserInputMappingEntry,
    ParserIssue,
    ParserIssueSeverity,
    ParserPipelineSummary,
    ParserResult,
    ParserResultSummary,
    create_parser_adapter_registry,
    build_fixture_parser_input_mapping,
    create_parser_input_contract,
    list_parser_adapters,
    plan_parser_execution,
    register_parser_adapter,
    resolve_parser_adapters,
    summarize_parser_pipeline,
    validate_parser_input_contract,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "ArtificialFixtureParser",
    "DefraDesnzParser",
    "ExampleInMemoryParser",
    "ExampleSourceSpecificParser",
    "ParserAdapter",
    "ParserAdapterRegistry",
    "ParserExecutionPlan",
    "ParserExecutionPlanStatus",
    "ParserInputContract",
    "ParserInputValidationIssue",
    "ParserInputValidationResult",
    "ParserInputMapping",
    "ParserInputMappingEntry",
    "ParserIssue",
    "ParserIssueSeverity",
    "ParserPipelineSummary",
    "ParserResult",
    "ParserResultSummary",
    "create_parser_adapter_registry",
    "create_parser_input_contract",
    "list_parser_adapters",
    "plan_parser_execution",
    "register_parser_adapter",
    "resolve_parser_adapters",
    "validate_parser_input_contract",
    "build_fixture_parser_input_mapping",
    "summarize_parser_pipeline",
)

EXPECTED_PUBLIC_EXPORTS = {
    "ArtificialFixtureParser": fixture_parser.ArtificialFixtureParser,
    "DefraDesnzParser": defra_desnz_parser.DefraDesnzParser,
    "ExampleInMemoryParser": example_parser.ExampleInMemoryParser,
    "ExampleSourceSpecificParser": (
        example_source_specific_parser.ExampleSourceSpecificParser
    ),
    "ParserAdapter": adapter.ParserAdapter,
    "ParserAdapterRegistry": adapter_registry.ParserAdapterRegistry,
    "ParserExecutionPlan": execution_plan.ParserExecutionPlan,
    "ParserExecutionPlanStatus": execution_plan.ParserExecutionPlanStatus,
    "ParserInputContract": input_contract.ParserInputContract,
    "ParserInputValidationIssue": input_contract.ParserInputValidationIssue,
    "ParserInputValidationResult": input_contract.ParserInputValidationResult,
    "ParserInputMapping": input_mapping.ParserInputMapping,
    "ParserInputMappingEntry": input_mapping.ParserInputMappingEntry,
    "ParserIssue": contracts.ParserIssue,
    "ParserIssueSeverity": contracts.ParserIssueSeverity,
    "ParserPipelineSummary": pipeline_summary.ParserPipelineSummary,
    "ParserResult": contracts.ParserResult,
    "ParserResultSummary": contracts.ParserResultSummary,
    "create_parser_adapter_registry": (
        adapter_registry.create_parser_adapter_registry
    ),
    "create_parser_input_contract": input_contract.create_parser_input_contract,
    "list_parser_adapters": adapter_registry.list_parser_adapters,
    "plan_parser_execution": execution_plan.plan_parser_execution,
    "register_parser_adapter": adapter_registry.register_parser_adapter,
    "resolve_parser_adapters": adapter_registry.resolve_parser_adapters,
    "validate_parser_input_contract": input_contract.validate_parser_input_contract,
    "build_fixture_parser_input_mapping": (
        input_mapping.build_fixture_parser_input_mapping
    ),
    "summarize_parser_pipeline": pipeline_summary.summarize_parser_pipeline,
}


def test_expected_parser_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "ArtificialFixtureParser": ArtificialFixtureParser,
        "DefraDesnzParser": DefraDesnzParser,
        "ExampleInMemoryParser": ExampleInMemoryParser,
        "ExampleSourceSpecificParser": ExampleSourceSpecificParser,
        "ParserAdapter": ParserAdapter,
        "ParserAdapterRegistry": ParserAdapterRegistry,
        "ParserExecutionPlan": ParserExecutionPlan,
        "ParserExecutionPlanStatus": ParserExecutionPlanStatus,
        "ParserInputContract": ParserInputContract,
        "ParserInputValidationIssue": ParserInputValidationIssue,
        "ParserInputValidationResult": ParserInputValidationResult,
        "ParserInputMapping": ParserInputMapping,
        "ParserInputMappingEntry": ParserInputMappingEntry,
        "ParserIssue": ParserIssue,
        "ParserIssueSeverity": ParserIssueSeverity,
        "ParserPipelineSummary": ParserPipelineSummary,
        "ParserResult": ParserResult,
        "ParserResultSummary": ParserResultSummary,
        "create_parser_adapter_registry": create_parser_adapter_registry,
        "create_parser_input_contract": create_parser_input_contract,
        "list_parser_adapters": list_parser_adapters,
        "plan_parser_execution": plan_parser_execution,
        "register_parser_adapter": register_parser_adapter,
        "resolve_parser_adapters": resolve_parser_adapters,
        "validate_parser_input_contract": validate_parser_input_contract,
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
    assert "contracts" not in parsers.__all__
    assert "defra_desnz_parser" not in parsers.__all__
    assert "example_parser" not in parsers.__all__
    assert "example_source_specific_parser" not in parsers.__all__
    assert "execution_plan" not in parsers.__all__
    assert "fixture_parser" not in parsers.__all__
    assert "input_contract" not in parsers.__all__
    assert "input_mapping" not in parsers.__all__
    assert "pipeline_summary" not in parsers.__all__
    assert all(not name.startswith("_") for name in parsers.__all__)
