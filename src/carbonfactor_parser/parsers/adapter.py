"""Parser adapter protocol boundary."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from carbonfactor_parser.parsers.contracts import ParserResult
from carbonfactor_parser.parsers.input_contract import ParserInputContract


@runtime_checkable
class ParserAdapter(Protocol):
    """Protocol for future source-specific parser adapters."""

    @property
    def source_family(self) -> str:
        """Return the source family handled by this adapter."""

    @property
    def supported_content_types(self) -> tuple[str, ...]:
        """Return content types the adapter may accept."""

    @property
    def supported_format_hints(self) -> tuple[str, ...]:
        """Return format hints the adapter may accept."""

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        """Return whether parser input metadata is compatible."""

    def parse(self, parser_input: ParserInputContract) -> ParserResult:
        """Future parser execution boundary."""
