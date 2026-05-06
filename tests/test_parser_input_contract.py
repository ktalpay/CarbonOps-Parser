from dataclasses import fields

from carbonfactor_parser.parsers import (
    ParserInputContract,
    create_parser_input_contract,
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
