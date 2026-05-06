"""Intentional public exports for parser contracts."""

from carbonfactor_parser.parsers.adapter import ParserAdapter
from carbonfactor_parser.parsers.adapter_registry import (
    ParserAdapterRegistry,
    create_parser_adapter_registry,
    list_parser_adapters,
    register_parser_adapter,
    resolve_parser_adapters,
)
from carbonfactor_parser.parsers.artificial_adapter import ArtificialParserAdapter
from carbonfactor_parser.parsers.contracts import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
    ParserResultSummary,
)
from carbonfactor_parser.parsers.defra_desnz_content_parser import (
    DEFRA_DESNZ_MINIMAL_CONTENT_HEADER,
    parse_defra_desnz_file_content,
)
from carbonfactor_parser.parsers.defra_desnz_adapter import DefraDesnzParserAdapter
from carbonfactor_parser.parsers.defra_desnz_parser import DefraDesnzParser
from carbonfactor_parser.parsers.example_parser import ExampleInMemoryParser
from carbonfactor_parser.parsers.example_source_specific_parser import (
    ExampleSourceSpecificParser,
)
from carbonfactor_parser.parsers.execution_plan import (
    ParserExecutionPlan,
    ParserExecutionPlanStatus,
    plan_parser_execution,
)
from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.execution_runner import run_parser_execution
from carbonfactor_parser.parsers.file_content_input import (
    ParserFileContentInput,
    ParserFileContentValidationIssue,
    ParserFileContentValidationResult,
    create_parser_file_content_input,
    validate_parser_file_content_input,
)
from carbonfactor_parser.parsers.fixture_parser import ArtificialFixtureParser
from carbonfactor_parser.parsers.input_contract import (
    ParserInputContract,
    ParserInputValidationIssue,
    ParserInputValidationResult,
    create_parser_input_contract,
    validate_parser_input_contract,
)
from carbonfactor_parser.parsers.input_mapping import (
    ParserInputMapping,
    ParserInputMappingEntry,
    build_fixture_parser_input_mapping,
)
from carbonfactor_parser.parsers.noop_adapter import NoopParserAdapter
from carbonfactor_parser.parsers.pipeline_summary import (
    ParserPipelineSummary,
    summarize_parser_pipeline,
)

__all__ = (
    "ArtificialFixtureParser",
    "ArtificialParserAdapter",
    "DEFRA_DESNZ_MINIMAL_CONTENT_HEADER",
    "DefraDesnzParserAdapter",
    "DefraDesnzParser",
    "ExampleInMemoryParser",
    "ExampleSourceSpecificParser",
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
    "ParserResult",
    "ParserResultSummary",
    "create_parser_adapter_registry",
    "create_parser_execution_result",
    "create_parser_file_content_input",
    "create_parser_input_contract",
    "list_parser_adapters",
    "plan_parser_execution",
    "parse_defra_desnz_file_content",
    "register_parser_adapter",
    "resolve_parser_adapters",
    "run_parser_execution",
    "validate_parser_file_content_input",
    "validate_parser_input_contract",
    "build_fixture_parser_input_mapping",
    "summarize_parser_pipeline",
)
