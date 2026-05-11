"""GHG Protocol parser adapter."""

from __future__ import annotations

from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.file_content_input import ParserFileContentInput
from carbonfactor_parser.parsers.ghg_protocol_content_parser import (
    parse_ghg_protocol_file_content,
)
from carbonfactor_parser.parsers.input_contract import ParserInputContract


class GHGProtocolParserAdapter:
    """GHG Protocol parser adapter for already-loaded content parsing."""

    source_family = "ghg_protocol"
    supported_content_types = (
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    supported_format_hints = ("csv", "xlsx")

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        """Return True for matching GHG Protocol parser input metadata."""

        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input: ParserInputContract) -> ParserExecutionResult:
        """Return unsupported until artifact file loading is explicitly wired."""

        return create_parser_execution_result(
            status=ParserExecutionResultStatus.UNSUPPORTED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_PARSER_REQUIRES_LOADED_CONTENT",
                    message=(
                        "GHG Protocol parser adapter requires caller-provided "
                        "content via parse_content."
                    ),
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="ghg_protocol_parser_adapter",
                ),
            ),
            parser_metadata={
                "adapter_kind": "source_specific_content_parser",
                "is_real_source_parser": True,
                "real_parsing_implemented": True,
                "requires_loaded_content": True,
            },
        )

    def parse_content(
        self,
        content_input: ParserFileContentInput,
    ) -> ParserExecutionResult:
        """Parse already-loaded GHG Protocol content."""

        return parse_ghg_protocol_file_content(content_input)
