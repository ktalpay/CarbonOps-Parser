"""Intentional public exports for parser contracts."""

from carbonfactor_parser.parsers.adapter import ParserAdapter
from carbonfactor_parser.parsers.contracts import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
    ParserResultSummary,
)
from carbonfactor_parser.parsers.defra_desnz_parser import DefraDesnzParser
from carbonfactor_parser.parsers.example_parser import ExampleInMemoryParser
from carbonfactor_parser.parsers.example_source_specific_parser import (
    ExampleSourceSpecificParser,
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
from carbonfactor_parser.parsers.pipeline_summary import (
    ParserPipelineSummary,
    summarize_parser_pipeline,
)

__all__ = (
    "ArtificialFixtureParser",
    "DefraDesnzParser",
    "ExampleInMemoryParser",
    "ExampleSourceSpecificParser",
    "ParserAdapter",
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
    "create_parser_input_contract",
    "validate_parser_input_contract",
    "build_fixture_parser_input_mapping",
    "summarize_parser_pipeline",
)
