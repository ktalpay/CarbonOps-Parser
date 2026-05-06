from carbonfactor_parser.source_adapters import (
    SourceAdapterExecutionResult,
    create_source_adapter_execution_result,
    has_errors,
    has_warnings,
    validate_source_adapter_execution_result,
)
from fakes import (
    make_adapter_parse_result,
    make_ingestion_run_summary,
    make_source_document,
)


def test_factory_returns_source_adapter_execution_result() -> None:
    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
    )

    assert isinstance(result, SourceAdapterExecutionResult)


def test_default_warnings_and_errors_are_empty_tuples() -> None:
    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
    )

    assert result.warnings == ()
    assert result.errors == ()


def test_list_warnings_and_errors_are_converted_to_tuples() -> None:
    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
        warnings=["first warning", "second warning"],
        errors=["first error", "second error"],
    )

    assert result.warnings == ("first warning", "second warning")
    assert result.errors == ("first error", "second error")


def test_tuple_warnings_and_errors_are_preserved() -> None:
    warnings = ("first warning", "second warning")
    errors = ("first error", "second error")

    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
        warnings=warnings,
        errors=errors,
    )

    assert result.warnings is warnings
    assert result.errors is errors


def test_warning_and_error_list_mutation_after_creation_does_not_mutate_result() -> None:
    warnings = ["first warning"]
    errors = ["first error"]

    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
        warnings=warnings,
        errors=errors,
    )
    warnings.append("second warning")
    errors.append("second error")

    assert result.warnings == ("first warning",)
    assert result.errors == ("first error",)


def test_source_objects_are_preserved_by_identity() -> None:
    document = make_source_document()
    parse_result = make_adapter_parse_result()
    ingestion_summary = make_ingestion_run_summary()

    result = create_source_adapter_execution_result(
        document=document,
        parse_result=parse_result,
        ingestion_summary=ingestion_summary,
    )

    assert result.document is document
    assert result.parse_result is parse_result
    assert result.ingestion_summary is ingestion_summary


def test_returned_result_passes_validation_for_valid_input() -> None:
    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
        warnings=("sample warning",),
        errors=(),
    )

    assert validate_source_adapter_execution_result(result) == []


def test_has_errors_and_has_warnings_work_with_factory_created_results() -> None:
    result = create_source_adapter_execution_result(
        document=make_source_document(),
        parse_result=make_adapter_parse_result(),
        ingestion_summary=make_ingestion_run_summary(),
        warnings=["sample warning"],
        errors=["sample error"],
    )

    assert has_warnings(result) is True
    assert has_errors(result) is True
