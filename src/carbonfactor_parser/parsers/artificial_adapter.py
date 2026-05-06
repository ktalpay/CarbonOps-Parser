"""Artificial parser adapter for deterministic boundary tests."""

from __future__ import annotations

from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.input_contract import ParserInputContract


class ArtificialParserAdapter:
    """In-memory parser adapter for demo and boundary tests only."""

    source_family = "artificial"
    supported_content_types = ("application/x-carbonops-artificial",)
    supported_format_hints = ("artificial",)

    def __init__(self, *, parsed_record_count: int = 1) -> None:
        if not isinstance(parsed_record_count, int) or parsed_record_count < 0:
            raise ValueError("parsed_record_count must be a non-negative integer.")
        self.parsed_record_count = parsed_record_count

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        """Return True for matching artificial parser input metadata only."""

        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input: ParserInputContract) -> ParserExecutionResult:
        """Return deterministic artificial parser execution metadata."""

        if not self.can_parse(parser_input):
            return create_parser_execution_result(
                status=ParserExecutionResultStatus.UNSUPPORTED,
                parser_input=parser_input,
                issues=(
                    ParserExecutionIssue(
                        code="ARTIFICIAL_PARSER_INPUT_UNSUPPORTED",
                        message=(
                            "ArtificialParserAdapter only supports artificial "
                            "parser input metadata."
                        ),
                        severity=ParserExecutionIssueSeverity.WARNING,
                        location="parser_input",
                    ),
                ),
                parser_metadata=_artificial_parser_metadata(),
            )

        return create_parser_execution_result(
            status=ParserExecutionResultStatus.SUCCESS,
            parser_input=parser_input,
            parsed_record_count=self.parsed_record_count,
            parser_metadata=_artificial_parser_metadata(),
        )


def _artificial_parser_metadata() -> dict[str, object]:
    return {
        "adapter_kind": "artificial",
        "is_real_source_parser": False,
        "record_count_source": "adapter_configuration",
    }
