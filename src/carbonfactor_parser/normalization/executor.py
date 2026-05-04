"""Artificial normalization executor skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.normalization.contracts import (
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.handoff import ParserNormalizationHandoff


@dataclass(frozen=True)
class ArtificialNormalizationExecutor:
    """Boundary skeleton that maps handoff metadata into artificial records."""

    def execute(self, handoff: ParserNormalizationHandoff) -> NormalizationResult:
        return NormalizationResult(
            records=tuple(
                NormalizedRecord(
                    record_id=entry.record_id,
                    fields=(
                        ("parser_record", entry.parser_record),
                        ("parser_source_reference", entry.source_reference),
                        ("handoff_source_reference", handoff.source_reference),
                        ("handoff_is_artificial", handoff.is_artificial),
                    ),
                    source_reference=entry.source_reference,
                    is_artificial=True,
                )
                for entry in handoff.entries
            )
        )
