from dataclasses import fields

from carbonfactor_parser.parsers import (
    ParserInputContract,
    ParserInputValidationIssue,
    ParserInputValidationResult,
    create_parser_input_contract,
    validate_parser_input_contract,
)


def test_parser_input_contract_preserves_required_fields() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
    )

    assert isinstance(parser_input, ParserInputContract)
    assert parser_input.source_family == "defra_desnz"
    assert parser_input.source_id == "defra_desnz"
    assert parser_input.acquisition_status == "acquired"
    assert (
        parser_input.artifact_reference
        == "data/source-acquisition/defra_desnz/source.csv"
    )


def test_parser_input_contract_allows_optional_metadata_to_be_omitted() -> None:
    parser_input = create_parser_input_contract(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        acquisition_status="not_implemented",
    )

    assert parser_input.artifact_reference is None
    assert parser_input.checksum_sha256 is None
    assert parser_input.content_type is None
    assert parser_input.format_hint is None
    assert parser_input.acquisition_run_id is None
    assert parser_input.run_metadata is None
    assert parser_input.manifest_metadata is None


def test_parser_input_contract_retains_acquisition_metadata() -> None:
    run_metadata = {
        "run_label": "static-run",
        "result_count": 1,
        "acquired_count": 1,
    }
    manifest_metadata = {
        "manifest_entry_count": 1,
        "manifest_path": None,
    }

    parser_input = create_parser_input_contract(
        source_family="ipcc_efdb",
        source_id="ipcc_efdb",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/ipcc_efdb/source.csv",
        checksum_sha256="b" * 64,
        content_type="text/csv",
        format_hint="csv",
        acquisition_run_id="static-run",
        run_metadata=run_metadata,
        manifest_metadata=manifest_metadata,
    )

    assert parser_input.checksum_sha256 == "b" * 64
    assert parser_input.content_type == "text/csv"
    assert parser_input.format_hint == "csv"
    assert parser_input.acquisition_status == "acquired"
    assert parser_input.acquisition_run_id == "static-run"
    assert parser_input.run_metadata == run_metadata
    assert parser_input.manifest_metadata == manifest_metadata


def test_parser_input_contract_copies_mapping_metadata() -> None:
    run_metadata = {"run_label": "before"}

    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        run_metadata=run_metadata,
    )
    run_metadata["run_label"] = "after"

    assert parser_input.run_metadata == {"run_label": "before"}


def test_parser_input_contract_creation_has_no_file_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_open(*args, **kwargs):
        raise AssertionError("parser input contract must not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(missing_artifact),
    )

    assert parser_input.artifact_reference == str(missing_artifact)
    assert not missing_artifact.exists()


def test_parser_input_contract_has_no_parser_or_normalization_output_fields() -> None:
    contract_field_names = {field.name for field in fields(ParserInputContract)}

    assert "records" not in contract_field_names
    assert "issues" not in contract_field_names
    assert "parser_output" not in contract_field_names
    assert "normalization_output" not in contract_field_names
    assert "normalization_records" not in contract_field_names
    assert "database_table" not in contract_field_names
    assert "database_record_id" not in contract_field_names


def test_parser_input_validation_accepts_valid_contract() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        checksum_sha256="c" * 64,
        content_type="text/csv",
        format_hint="csv",
        acquisition_run_id="static-run",
        run_metadata={"result_count": 1},
        manifest_metadata={"manifest_entry_count": 1},
    )

    result = validate_parser_input_contract(parser_input)

    assert isinstance(result, ParserInputValidationResult)
    assert result.is_valid is True
    assert result.issues == ()


def test_parser_input_validation_reports_missing_source_family() -> None:
    parser_input = create_parser_input_contract(
        source_family=" ",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_INPUT_MISSING_SOURCE_FAMILY",)


def test_parser_input_validation_reports_missing_source_id() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_INPUT_MISSING_SOURCE_ID",)


def test_parser_input_validation_reports_missing_artifact_reference() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=" ",
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_INPUT_MISSING_ARTIFACT_REFERENCE",)


def test_parser_input_validation_reports_blank_optional_metadata_when_provided() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status=" ",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        checksum_sha256="",
        content_type=" ",
        format_hint="",
        acquisition_run_id=" ",
        run_metadata={},
        manifest_metadata={},
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_MISSING_ACQUISITION_STATUS",
        "PARSER_INPUT_BLANK_CHECKSUM_SHA256",
        "PARSER_INPUT_BLANK_CONTENT_TYPE",
        "PARSER_INPUT_BLANK_FORMAT_HINT",
        "PARSER_INPUT_BLANK_ACQUISITION_RUN_ID",
        "PARSER_INPUT_EMPTY_RUN_METADATA",
        "PARSER_INPUT_EMPTY_MANIFEST_METADATA",
    )


def test_parser_input_validation_reports_non_mapping_metadata_when_provided() -> None:
    parser_input = ParserInputContract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        run_metadata="static-run",  # type: ignore[arg-type]
        manifest_metadata="manifest",  # type: ignore[arg-type]
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_EMPTY_RUN_METADATA",
        "PARSER_INPUT_EMPTY_MANIFEST_METADATA",
    )


def test_parser_input_validation_allows_absent_optional_metadata() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
    )

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is True
    assert result.issues == ()


def test_parser_input_validation_has_no_file_side_effects(monkeypatch, tmp_path) -> None:
    missing_artifact = tmp_path / "missing.csv"
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(missing_artifact),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("parser input validation must not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = validate_parser_input_contract(parser_input)

    assert result.is_valid is True
    assert not missing_artifact.exists()


def test_parser_input_validation_issue_shape_is_structured() -> None:
    parser_input = create_parser_input_contract(
        source_family="",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
    )

    issue = validate_parser_input_contract(parser_input).issues[0]

    assert isinstance(issue, ParserInputValidationIssue)
    assert issue.code == "PARSER_INPUT_MISSING_SOURCE_FAMILY"
    assert issue.field_name == "source_family"
    assert issue.severity == "error"
    assert issue.message == "source_family must be a non-empty string."


def _issue_codes(result: ParserInputValidationResult) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
