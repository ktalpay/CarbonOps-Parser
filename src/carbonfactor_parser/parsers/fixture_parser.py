"""Artificial fixture parser skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.parsers.contracts import ParserResult
from carbonfactor_parser.parsers.input_mapping import ParserInputMapping
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


@dataclass(frozen=True)
class ArtificialFixtureParser:
    """Generate artificial records from fixture input mapping metadata."""

    source_family: SourceFamily = SourceFamily.DEFRA_DESNZ
    source_name: str = "fixture:artificial_fixture_parser"

    def parse_mapping(self, mapping: ParserInputMapping) -> ParserResult:
        return ParserResult(
            source_document=self._source_document(mapping),
            records=tuple(
                {
                    "record_id": entry.document_id,
                    "file_name": entry.file_name,
                    "file_extension": entry.file_extension,
                    "source_label": entry.source_name,
                    "value_label": entry.parser_hint or "artificial-fixture",
                }
                for entry in mapping.entries
            ),
        )

    def _source_document(self, mapping: ParserInputMapping) -> SourceDocument:
        return SourceDocument(
            source_family=mapping.source_family or self.source_family,
            source_name=mapping.source_name or self.source_name,
        )
