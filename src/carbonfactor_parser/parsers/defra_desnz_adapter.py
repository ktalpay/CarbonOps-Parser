"""DEFRA/DESNZ parser adapter skeleton."""

from __future__ import annotations

from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.input_contract import ParserInputContract


class DefraDesnzParserAdapter:
    """DEFRA/DESNZ parser adapter skeleton without real parsing."""

    source_family = "defra_desnz"
    supported_content_types = (
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    supported_format_hints = ("csv", "xlsx")

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        """Return True for matching DEFRA/DESNZ parser input metadata only."""

        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input: ParserInputContract) -> ParserExecutionResult:
        """Return a skeleton result until DEFRA/DESNZ parsing is implemented."""

        return create_parser_execution_result(
            status=ParserExecutionResultStatus.UNSUPPORTED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_PARSER_NOT_IMPLEMENTED",
                    message=(
                        "DEFRA/DESNZ parser adapter is a skeleton; real parsing "
                        "is not implemented yet."
                    ),
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="defra_desnz_parser_adapter",
                ),
            ),
            parser_metadata={
                "adapter_kind": "source_specific_skeleton",
                "is_real_source_parser": False,
                "real_parsing_implemented": False,
            },
        )
