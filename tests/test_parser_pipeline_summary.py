from pathlib import Path

from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    ParserInputMapping,
    ParserIssue,
    ParserIssueSeverity,
    ParserPipelineSummary,
    ParserResult,
    build_fixture_parser_input_mapping,
    summarize_parser_pipeline,
)
from carbonfactor_parser.source_adapters import (
    DefraDesnzSourceAdapter,
    SourceDocument,
    SourceFamily,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[0] / "fixtures" / "source_documents" / "defra_desnz"
)

EXPECTED_DEFRA_DESNZ_FIXTURE_SOURCE_NAMES = (
    "defra_desnz:defra_desnz_malformed_factors.csv",
    "defra_desnz:defra_desnz_metadata.json",
    "defra_desnz:defra_desnz_normalized_factors.csv",
    "defra_desnz:defra_desnz_sample_factors.csv",
)


def _document(
    *,
    source_family: SourceFamily = SourceFamily.DEFRA_DESNZ,
    source_name: str = "fixture:sample.csv",
    file_reference: str | None = None,
) -> SourceDocument:
    return SourceDocument(
        source_family=source_family,
        source_name=source_name,
        file_reference=file_reference,
    )


def _empty_mapping() -> ParserInputMapping:
    return ParserInputMapping(
        source_family=None,
        source_name="fixture_parser_input_mapping",
        document_count=0,
        entries=(),
    )


def _empty_parser_result() -> ParserResult:
    return ParserResult(
        source_document=_document(source_name="fixture:parser-result"),
    )


def test_summary_handles_empty_pipeline_objects() -> None:
    summary = summarize_parser_pipeline((), _empty_mapping(), _empty_parser_result())

    assert summary == ParserPipelineSummary(
        discovered_document_count=0,
        mapping_entry_count=0,
        parser_record_count=0,
        parser_warning_count=0,
        parser_error_count=0,
        has_discovered_documents=False,
        has_mapping_entries=False,
        has_parser_records=False,
        has_parser_warnings=False,
        has_parser_errors=False,
        is_clean=True,
    )


def test_summary_counts_discovered_documents() -> None:
    documents = (
        _document(source_name="fixture:beta.csv"),
        _document(source_name="fixture:alpha.json"),
    )

    summary = summarize_parser_pipeline(
        documents,
        _empty_mapping(),
        _empty_parser_result(),
    )

    assert summary.discovered_document_count == 2
    assert summary.has_discovered_documents is True
    assert summary.source_families == (SourceFamily.DEFRA_DESNZ,)
    assert summary.source_names == ("fixture:alpha.json", "fixture:beta.csv")


def test_summary_counts_mapping_entries() -> None:
    documents = (
        _document(
            source_name="fixture:source.csv",
            file_reference=str(FIXTURE_DIRECTORY / "source.csv"),
        ),
    )
    mapping = build_fixture_parser_input_mapping(documents)

    summary = summarize_parser_pipeline((), mapping, _empty_parser_result())

    assert summary.mapping_entry_count == 1
    assert summary.has_mapping_entries is True
    assert summary.source_families == (SourceFamily.DEFRA_DESNZ,)
    assert summary.source_names == ("fixture:source.csv",)


def test_summary_counts_parser_records() -> None:
    parser_result = ParserResult(
        source_document=_document(),
        records=(
            {"record_id": "record-001"},
            {"record_id": "record-002"},
        ),
    )

    summary = summarize_parser_pipeline((), _empty_mapping(), parser_result)

    assert summary.parser_record_count == 2
    assert summary.has_parser_records is True


def test_summary_counts_parser_warnings_and_errors() -> None:
    parser_result = ParserResult(
        source_document=_document(),
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

    summary = summarize_parser_pipeline((), _empty_mapping(), parser_result)

    assert summary.parser_warning_count == 1
    assert summary.parser_error_count == 1


def test_summary_boolean_flags_behave_correctly() -> None:
    parser_result = ParserResult(
        source_document=_document(),
        records=({"record_id": "record-001"},),
        issues=(
            ParserIssue(
                code="sample-warning",
                message="Sample warning",
                severity=ParserIssueSeverity.WARNING,
            ),
        ),
    )

    summary = summarize_parser_pipeline(
        (_document(),),
        build_fixture_parser_input_mapping((_document(),)),
        parser_result,
    )

    assert summary.has_discovered_documents is True
    assert summary.has_mapping_entries is True
    assert summary.has_parser_records is True
    assert summary.has_parser_warnings is True
    assert summary.has_parser_errors is False
    assert summary.is_clean is False


def test_summary_works_with_existing_fixture_only_pipeline_components() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents
    mapping = build_fixture_parser_input_mapping(
        documents,
        parser_hint="artificial-fixture",
    )
    parser_result = ArtificialFixtureParser().parse_mapping(mapping)

    summary = summarize_parser_pipeline(documents, mapping, parser_result)

    assert summary.discovered_document_count == 4
    assert summary.mapping_entry_count == 4
    assert summary.parser_record_count == 4
    assert summary.parser_warning_count == 0
    assert summary.parser_error_count == 0
    assert summary.has_discovered_documents is True
    assert summary.has_mapping_entries is True
    assert summary.has_parser_records is True
    assert summary.is_clean is True
    assert summary.source_families == (SourceFamily.DEFRA_DESNZ,)
    assert summary.source_names == EXPECTED_DEFRA_DESNZ_FIXTURE_SOURCE_NAMES


def test_summary_does_not_perform_file_io(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"
    document = _document(
        source_name="fixture:missing.csv",
        file_reference=str(missing_path),
    )
    mapping = build_fixture_parser_input_mapping((document,))
    parser_result = ParserResult(
        source_document=document,
        records=({"record_id": "fixture:missing.csv"},),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("summary helper should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    summary = summarize_parser_pipeline((document,), mapping, parser_result)

    assert summary.parser_record_count == 1
    assert not missing_path.exists()
