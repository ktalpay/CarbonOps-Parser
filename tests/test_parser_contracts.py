from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.parsers import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
    ParserResultSummary,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def _source_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:source.csv",
        file_reference="fixtures/source.csv",
    )


def test_parser_issue_can_represent_warning_and_error() -> None:
    warning = ParserIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=ParserIssueSeverity.WARNING,
    )
    error = ParserIssue(
        code="fixture_error",
        message="Fixture error",
        severity=ParserIssueSeverity.ERROR,
        location="row 1",
        context={"field": "value"},
    )

    assert warning.severity == ParserIssueSeverity.WARNING
    assert error.severity == ParserIssueSeverity.ERROR
    assert error.location == "row 1"
    assert error.context == {"field": "value"}


def test_parser_result_can_be_created_with_no_records_or_issues() -> None:
    result = ParserResult(source_document=_source_document())

    assert result.records == ()
    assert result.issues == ()
    assert isinstance(result.summary, ParserResultSummary)


def test_parser_result_summary_counts_records_warnings_and_errors() -> None:
    result = ParserResult(
        source_document=_source_document(),
        records=({"row": "one"}, {"row": "two"}),
        issues=(
            ParserIssue(
                code="fixture_warning",
                message="Fixture warning",
                severity=ParserIssueSeverity.WARNING,
            ),
            ParserIssue(
                code="fixture_error",
                message="Fixture error",
                severity=ParserIssueSeverity.ERROR,
            ),
        ),
    )

    summary = result.summary

    assert summary.record_count == 2
    assert summary.warning_count == 1
    assert summary.error_count == 1


def test_parser_result_summary_boolean_flags_for_clean_result() -> None:
    summary = ParserResult(source_document=_source_document()).summary

    assert summary.has_records is False
    assert summary.has_warnings is False
    assert summary.has_errors is False
    assert summary.is_clean is True


def test_parser_result_summary_boolean_flags_for_non_clean_result() -> None:
    result = ParserResult(
        source_document=_source_document(),
        records=({"row": "one"},),
        issues=(
            ParserIssue(
                code="fixture_warning",
                message="Fixture warning",
                severity=ParserIssueSeverity.WARNING,
            ),
        ),
    )

    summary = result.summary

    assert summary.has_records is True
    assert summary.has_warnings is True
    assert summary.has_errors is False
    assert summary.is_clean is False


def test_parser_result_records_and_issues_are_tuple_based() -> None:
    issue = ParserIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=ParserIssueSeverity.WARNING,
    )
    result = ParserResult(
        source_document=_source_document(),
        records=({"row": "one"},),
        issues=(issue,),
    )

    assert isinstance(result.records, tuple)
    assert isinstance(result.issues, tuple)


def test_parser_contract_dataclasses_are_frozen() -> None:
    issue = ParserIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=ParserIssueSeverity.WARNING,
    )
    result = ParserResult(source_document=_source_document())

    with pytest.raises(FrozenInstanceError):
        issue.code = "changed"
    with pytest.raises(FrozenInstanceError):
        result.records = ()


def test_parser_contracts_do_not_require_file_io(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"
    result = ParserResult(
        source_document=SourceDocument(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="fixture:missing.csv",
            file_reference=str(missing_path),
        )
    )

    assert result.summary.is_clean is True
    assert not missing_path.exists()
