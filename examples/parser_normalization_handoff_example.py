"""In-memory parser-to-normalization handoff example."""

from __future__ import annotations

from carbonfactor_parser.normalization import (
    ParserNormalizationHandoff,
    build_parser_normalization_handoff,
)
from carbonfactor_parser.parsers import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def build_parser_normalization_handoff_example() -> dict[str, object]:
    parser_result = ParserResult(
        source_document=_example_source_document(),
        records=(
            {
                "record_id": "record-001",
                "field_name": "alpha",
                "value_label": "one",
            },
            {
                "field_name": "beta",
                "value_label": "two",
            },
        ),
        issues=(
            ParserIssue(
                code="example_warning",
                message="Artificial parser warning",
                severity=ParserIssueSeverity.WARNING,
                location="record 2",
            ),
        ),
    )
    handoff = build_parser_normalization_handoff(parser_result)
    return _handoff_to_dict(handoff)


def _example_source_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:artificial_parser_source",
        file_reference="fixtures/artificial_parser_source.txt",
    )


def _handoff_to_dict(
    handoff: ParserNormalizationHandoff,
) -> dict[str, object]:
    return {
        "parser_record_count": handoff.parser_record_count,
        "handoff_entry_count": len(handoff.entries),
        "issue_count": handoff.issue_count,
        "source_reference": handoff.source_reference,
        "is_artificial": handoff.is_artificial,
        "entries": tuple(
            {
                "record_id": entry.record_id,
                "parser_record": entry.parser_record,
                "source_reference": entry.source_reference,
                "is_artificial": entry.is_artificial,
            }
            for entry in handoff.entries
        ),
    }
