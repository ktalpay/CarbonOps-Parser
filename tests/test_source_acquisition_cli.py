"""Tests for source acquisition CLI skeleton."""

from __future__ import annotations

import json

import pytest

from carbonfactor_parser.source_acquisition.cli import main


def test_cli_list_returns_zero_and_prints_default_sources(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["list"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ghg_protocol" in captured.out
    assert "defra_desnz" in captured.out
    assert "ipcc_efdb" in captured.out


def test_cli_list_json_output_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["list", "--output-format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert [entry["source_id"] for entry in payload["sources"]] == [
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    ]


def test_cli_run_returns_zero_and_prints_noop_counts(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["run"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "acquired_count=0" in captured.out
    assert "failed_count=0" in captured.out
    assert "skipped_count=3" in captured.out


def test_cli_run_json_output_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["run", "--output-format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["acquired_count"] == 0
    assert payload["failed_count"] == 0
    assert payload["skipped_count"] == 3
    assert payload["manifest_path"] is None
    assert [entry["source_id"] for entry in payload["results"]] == [
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    ]


def test_cli_run_with_manifest_path_writes_local_manifest(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    manifest_path = tmp_path / "acquisition-manifest.json"

    exit_code = main(
        [
            "run",
            "--manifest-path",
            str(manifest_path),
            "--output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert manifest_path.exists()

    payload = json.loads(captured.out)
    assert payload["manifest_path"] == str(manifest_path)

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [entry["source_id"] for entry in manifest_payload] == [
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    ]
    assert all(entry["status"] == "not_implemented" for entry in manifest_payload)


def test_cli_invalid_usage_raises_system_exit() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code != 0


def test_cli_invalid_output_format_raises_system_exit() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["list", "--output-format", "yaml"])

    assert exc_info.value.code != 0
