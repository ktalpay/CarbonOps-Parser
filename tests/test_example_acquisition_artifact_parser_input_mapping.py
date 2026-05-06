from examples.example_acquisition_artifact_parser_input_mapping import (
    build_acquisition_artifact_parser_input_mapping_example,
)


def _parser_input() -> dict[str, object]:
    result = build_acquisition_artifact_parser_input_mapping_example()
    parser_input = result["parser_input"]

    assert isinstance(parser_input, dict)
    return parser_input


def test_example_preserves_source_family_and_source_id() -> None:
    parser_input = _parser_input()

    assert parser_input["source_family"] == "defra_desnz"
    assert parser_input["source_id"] == "defra_desnz"


def test_example_maps_local_artifact_reference() -> None:
    parser_input = _parser_input()

    assert (
        parser_input["artifact_reference"]
        == "data/source-acquisition/defra_desnz/example-factors.csv"
    )
    assert parser_input["manifest_metadata"]["local_path"] == parser_input[
        "artifact_reference"
    ]


def test_example_preserves_checksum_metadata_when_available() -> None:
    parser_input = _parser_input()

    assert parser_input["checksum_sha256"] == "a" * 64
    assert parser_input["manifest_metadata"]["checksum_sha256"] == "a" * 64


def test_example_preserves_content_type_and_format_hint() -> None:
    parser_input = _parser_input()

    assert parser_input["content_type"] == "text/csv"
    assert parser_input["format_hint"] == "csv"
    assert parser_input["manifest_metadata"]["content_type"] == "text/csv"


def test_example_represents_acquisition_status_and_run_metadata() -> None:
    parser_input = _parser_input()
    run_metadata = parser_input["run_metadata"]

    assert parser_input["acquisition_status"] == "acquired"
    assert parser_input["manifest_metadata"]["status"] == "acquired"
    assert run_metadata == {
        "run_label": "static-example-run",
        "result_count": 1,
        "manifest_entry_count": 1,
        "manifest_path": None,
        "acquired_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
    }


def test_example_produces_no_parser_or_normalization_output() -> None:
    result = build_acquisition_artifact_parser_input_mapping_example()

    assert result["parser_output_produced"] is False
    assert result["normalization_output_produced"] is False
    assert "parser_output" not in result
    assert "normalization_output" not in result
    assert result["parser_input"]["parser_boundary"] == "future_parser_input"
