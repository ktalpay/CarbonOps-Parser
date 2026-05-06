from carbonfactor_parser.normalization import (
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_parser_normalization_handoff,
)
from carbonfactor_parser.parsers import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def _source_document(
    *,
    source_name: str = "fixture:parser_source",
    file_reference: str | None = "fixtures/parser_source.txt",
) -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name=source_name,
        file_reference=file_reference,
    )


def test_handoff_can_be_created_from_empty_parser_result() -> None:
    parser_result = ParserResult(source_document=_source_document())

    handoff = build_parser_normalization_handoff(parser_result)

    assert isinstance(handoff, ParserNormalizationHandoff)
    assert handoff.parser_record_count == 0
    assert handoff.issue_count == 0
    assert handoff.entries == ()
    assert handoff.source_reference == "fixture:parser_source"
    assert handoff.is_artificial is True


def test_handoff_can_be_created_from_generic_artificial_records() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        records=(
            {"record_id": "record-001", "field_name": "alpha"},
            {"field_name": "beta", "value_label": "two"},
        ),
    )

    handoff = build_parser_normalization_handoff(parser_result)

    assert handoff.parser_record_count == 2
    assert len(handoff.entries) == 2
    assert all(
        isinstance(entry, ParserNormalizationHandoffEntry)
        for entry in handoff.entries
    )


def test_handoff_entry_ordering_is_deterministic() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        records=(
            {"value_label": "two", "field_name": "beta"},
            {"field_name": "alpha", "value_label": "one"},
        ),
    )

    first = build_parser_normalization_handoff(parser_result)
    second = build_parser_normalization_handoff(parser_result)

    assert first == second
    assert first.entries[0].parser_record == (
        ("field_name", "beta"),
        ("value_label", "two"),
    )
    assert first.entries[1].parser_record == (
        ("field_name", "alpha"),
        ("value_label", "one"),
    )


def test_handoff_record_ids_are_stable_and_deterministic() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        records=(
            {"record_id": "record-001", "field_name": "alpha"},
            {"field_name": "beta"},
            {"record_id": " ", "field_name": "gamma"},
        ),
    )

    handoff = build_parser_normalization_handoff(parser_result)

    assert [entry.record_id for entry in handoff.entries] == [
        "record-001",
        "parser-record-002",
        "parser-record-003",
    ]


def test_handoff_preserves_generic_parser_record_data_without_converting_it() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        records=(
            {
                "field_name": "alpha",
                "value_label": "one",
                "count": 2,
                "is_sample": True,
            },
        ),
    )

    handoff = build_parser_normalization_handoff(parser_result)

    assert handoff.entries[0].parser_record == (
        ("count", 2),
        ("field_name", "alpha"),
        ("is_sample", True),
        ("value_label", "one"),
    )


def test_handoff_counts_parser_issues_without_interpreting_them() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        issues=(
            ParserIssue(
                code="sample-warning",
                message="Sample warning",
                severity=ParserIssueSeverity.WARNING,
            ),
            ParserIssue(
                code="sample-error",
                message="Sample error",
                severity=ParserIssueSeverity.ERROR,
            ),
        ),
    )

    handoff = build_parser_normalization_handoff(parser_result)

    assert handoff.issue_count == 2
    assert handoff.entries == ()


def test_handoff_does_not_perform_unit_conversion_or_correctness_validation() -> None:
    parser_result = ParserResult(
        source_document=_source_document(),
        records=(
            {
                "record_id": "record-001",
                "value_label": "sample text",
                "unit_label": "uninterpreted label",
            },
        ),
    )

    handoff = build_parser_normalization_handoff(parser_result)
    handoff_text = str(handoff).lower()

    assert handoff.entries[0].parser_record == (
        ("record_id", "record-001"),
        ("unit_label", "uninterpreted label"),
        ("value_label", "sample text"),
    )
    assert "converted" not in handoff_text
    assert "correct" not in handoff_text


def test_handoff_does_not_require_file_io(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "parser_source.txt"
    parser_result = ParserResult(
        source_document=_source_document(
            source_name="fixture:missing_source",
            file_reference=str(missing_path),
        ),
        records=({"field_name": "alpha"},),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("handoff helper should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    handoff = build_parser_normalization_handoff(parser_result)

    assert handoff.parser_record_count == 1
    assert not missing_path.exists()
