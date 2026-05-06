"""No-op parser adapter boundary implementation."""

from __future__ import annotations

from carbonfactor_parser.parsers.contracts import ParserResult
from carbonfactor_parser.parsers.input_contract import ParserInputContract


class NoopParserAdapter:
    """Metadata-only parser adapter for planning and registry tests."""

    source_family = "noop"
    supported_content_types = ("application/x-carbonops-noop",)
    supported_format_hints = ("noop",)

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        """Return True for matching no-op parser input metadata only."""

        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input: ParserInputContract) -> ParserResult:
        """Refuse parser execution because this adapter is no-op only."""

        raise NotImplementedError(
            "NoopParserAdapter does not perform parser execution or produce parser output.",
        )
