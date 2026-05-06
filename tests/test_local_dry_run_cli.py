import inspect
import json
import sqlite3
import urllib.request
from pathlib import Path

import pytest

import carbonfactor_parser.cli as parser_cli
from carbonfactor_parser.pipeline import (
    LocalFilePersistenceDryRunResult,
    LocalFilePersistenceDryRunStatus,
)


def test_local_dry_run_cli_valid_fixture_returns_success_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(file_path),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--content-type",
            "text/csv",
            "--format-hint",
            "csv",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=success" in captured.out
    assert "parsed_record_count=1" in captured.out
    assert "normalization_record_count=1" in captured.out
    assert "persistence_input_record_count=1" in captured.out
    assert "ddl_preview_present=True" in captured.out
    assert "issue_count=0" in captured.out


def test_local_dry_run_cli_calls_existing_pipeline_helper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = tmp_path / "fixture.csv"
    calls: list[dict[str, object]] = []

    def fake_dry_run(**kwargs: object) -> LocalFilePersistenceDryRunResult:
        calls.append(kwargs)
        return LocalFilePersistenceDryRunResult(
            status=LocalFilePersistenceDryRunStatus.SUCCESS,
            source_family=str(kwargs["source_family"]),
            source_id=str(kwargs["source_id"]),
            local_path=str(kwargs["local_path"]),
            ddl_preview="-- preview",
        )

    monkeypatch.setattr(
        parser_cli,
        "run_local_file_normalized_persistence_dry_run",
        fake_dry_run,
    )

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(file_path),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--format-hint",
            "csv",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [
        {
            "local_path": file_path,
            "source_family": "defra_desnz",
            "source_id": "source-001",
            "content_type": None,
            "format_hint": "csv",
        },
    ]
    assert "status=success" in captured.out


def test_local_dry_run_cli_missing_file_returns_failure_and_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(tmp_path / "missing.csv"),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--content-type",
            "text/csv",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=failed" in captured.out
    assert "parsed_record_count=None" in captured.out
    assert "persistence_input_record_count=None" in captured.out
    assert "ddl_preview_present=False" in captured.out
    assert "load | error | PARSER_FILE_CONTENT_LOAD_NOT_FOUND" in captured.out


def test_local_dry_run_cli_invalid_parser_content_returns_failure_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(tmp_path, "wrong,header\n1,Electricity\n")

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(file_path),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--format-hint",
            "csv",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=failed" in captured.out
    assert "parse | error | DEFRA_DESNZ_CONTENT_INVALID_HEADER" in captured.out


def test_local_dry_run_cli_no_records_returns_nonzero_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(tmp_path, "factor_id,factor_name,unit\n")

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(file_path),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--content-type",
            "text/csv",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=no_records" in captured.out
    assert "parsed_record_count=0" in captured.out
    assert "persistence_input_record_count=None" in captured.out


def test_local_dry_run_cli_text_output_is_deterministic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )
    args = [
        "local-dry-run",
        "--local-path",
        str(file_path),
        "--source-family",
        "defra_desnz",
        "--source-id",
        "source-001",
        "--format-hint",
        "csv",
    ]

    first_exit = parser_cli.main(args)
    first_output = capsys.readouterr().out
    second_exit = parser_cli.main(args)
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert second_exit == 0
    assert first_output == second_output


def test_local_dry_run_cli_json_output_is_valid_and_deterministic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )
    args = [
        "local-dry-run",
        "--local-path",
        str(file_path),
        "--source-family",
        "defra_desnz",
        "--source-id",
        "source-001",
        "--content-type",
        "text/csv",
        "--output-format",
        "json",
    ]

    first_exit = parser_cli.main(args)
    first_output = capsys.readouterr().out
    second_exit = parser_cli.main(args)
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert second_exit == 0
    assert first_output == second_output

    payload = json.loads(first_output)
    assert payload["status"] == "success"
    assert payload["parsed_record_count"] == 1
    assert payload["normalization_record_count"] == 1
    assert payload["persistence_input_record_count"] == 1
    assert payload["ddl_preview_present"] is True
    assert "CREATE TABLE normalized_records" in payload["ddl_preview"]
    assert payload["issues"] == []


def test_local_dry_run_cli_requires_content_type_or_format_hint(
    tmp_path: Path,
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        parser_cli.main(
            [
                "local-dry-run",
                "--local-path",
                str(tmp_path / "fixture.csv"),
                "--source-family",
                "defra_desnz",
                "--source-id",
                "source-001",
            ],
        )

    assert excinfo.value.code == 2


def test_local_dry_run_cli_has_no_db_sql_or_network_behavior(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("CLI must not connect to a database")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("CLI must not perform network calls")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(file_path),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "source-001",
            "--content-type",
            "text/csv",
        ],
    )

    assert exit_code == 0


def test_local_dry_run_cli_does_not_scan_directories_or_load_config() -> None:
    module_source = inspect.getsource(parser_cli).lower()

    assert "source_acquisition" not in module_source
    assert "config" not in module_source
    assert "glob(" not in module_source
    assert "rglob(" not in module_source
    assert "iterdir(" not in module_source
    assert "scandir" not in module_source
    assert "walk(" not in module_source
    assert "psycopg" not in module_source
    assert "sqlalchemy" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert ".execute" not in module_source


def _write_fixture(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "defra_fixture.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path
