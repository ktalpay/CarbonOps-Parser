import inspect
import json
import sqlite3
import urllib.request
from pathlib import Path

import pytest

import carbonfactor_parser.cli as parser_cli
from carbonfactor_parser.persistence import (
    PersistenceResultStatus,
    PostgreSQLPersistenceRepository,
    build_postgresql_persistence_preview,
)
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
    assert captured.out == (
        "status=success\n"
        "parsed_record_count=1\n"
        "normalization_record_count=1\n"
        "persistence_input_record_count=1\n"
        "ddl_preview_present=True\n"
        "issue_count=0\n"
    )
    assert "postgresql_preview" not in captured.out


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
    assert "postgresql_persistence_preview" not in payload


def test_local_dry_run_cli_text_output_includes_postgresql_preview_with_flag(
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
            "--include-postgresql-preview",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=success" in captured.out
    assert "postgresql_preview_included=True" in captured.out
    assert "postgresql_preview_status=ready" in captured.out
    assert "postgresql_preview_only=True" in captured.out
    assert "postgresql_preview_sql_execution=False" in captured.out
    assert "postgresql_preview_database_connection=False" in captured.out
    assert "postgresql_preview_target_table=normalized_records" in captured.out
    assert "postgresql_preview_record_count=1" in captured.out
    assert (
        "postgresql_preview_sql=INSERT INTO normalized_records "
        "(source_family, source_id, record_id"
    ) in captured.out
    assert (
        'postgresql_preview_ordered_columns=["source_family","source_id",'
        '"record_id","record_index","row_number","normalized_fields"'
    ) in captured.out
    assert '"factor_name","Electricity"' in captured.out
    assert (
        'postgresql_preview_idempotency_key_fields=["source_family",'
        '"source_id","record_id","source_artifact_reference",'
        '"source_checksum_sha256"]'
    ) in captured.out
    assert (
        'postgresql_preview_conflict_target_fields=["source_family",'
        '"source_id","record_id","source_artifact_reference",'
        '"source_checksum_sha256"]'
    ) in captured.out
    assert "postgresql_preview_issue_count=0" in captured.out


def test_local_dry_run_cli_json_output_includes_postgresql_preview_with_flag(
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
            "--output-format",
            "json",
            "--include-postgresql-preview",
        ],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    postgresql_preview = payload["postgresql_persistence_preview"]

    assert exit_code == 0
    assert postgresql_preview["included"] is True
    assert postgresql_preview["preview_only"] is True
    assert postgresql_preview["sql_execution"] is False
    assert postgresql_preview["database_connection"] is False
    assert postgresql_preview["status"] == "ready"
    assert postgresql_preview["target_table"] == "normalized_records"
    assert postgresql_preview["record_count"] == 1
    assert postgresql_preview["sql"] == (
        "INSERT INTO normalized_records "
        "(source_family, source_id, record_id, record_index, row_number, "
        "normalized_fields, source_reference, source_artifact_reference, "
        "source_checksum_sha256, parser_metadata, normalization_metadata, "
        "created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    assert postgresql_preview["ordered_columns"] == [
        "source_family",
        "source_id",
        "record_id",
        "record_index",
        "row_number",
        "normalized_fields",
        "source_reference",
        "source_artifact_reference",
        "source_checksum_sha256",
        "parser_metadata",
        "normalization_metadata",
        "created_at",
        "updated_at",
    ]
    parameter_row = postgresql_preview["parameter_rows"][0]
    values_by_column = dict(zip(postgresql_preview["ordered_columns"], parameter_row))
    assert values_by_column["normalized_fields"] == [
        ["source_family", "defra_desnz"],
        ["source_id", "source-001"],
        ["record_index", 1],
        ["row_number", 2],
        ["factor_id", "1"],
        ["factor_name", "Electricity"],
        ["unit", "kWh"],
    ]
    assert postgresql_preview["idempotency_key_fields"] == [
        "source_family",
        "source_id",
        "record_id",
        "source_artifact_reference",
        "source_checksum_sha256",
    ]
    assert postgresql_preview["conflict_target_fields"] == [
        "source_family",
        "source_id",
        "record_id",
        "source_artifact_reference",
        "source_checksum_sha256",
    ]
    assert postgresql_preview["issues"] == []


def test_local_dry_run_cli_postgresql_preview_matches_preview_layer(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )
    dry_run_result = parser_cli.run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint=None,
    )
    preview_result = build_postgresql_persistence_preview(
        dry_run_result.persistence_input,
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
            "--output-format",
            "json",
            "--include-postgresql-preview",
        ],
    )

    captured = capsys.readouterr()
    postgresql_preview = json.loads(captured.out)["postgresql_persistence_preview"]
    assert exit_code == 0
    assert postgresql_preview["sql"] == preview_result.preview.sql
    assert postgresql_preview["target_table"] == (
        preview_result.preview.target_table_name
    )
    assert postgresql_preview["ordered_columns"] == list(
        preview_result.preview.column_names,
    )
    assert postgresql_preview["record_count"] == preview_result.preview.record_count


def test_local_dry_run_cli_postgresql_preview_delegates_to_preview_layer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )
    calls = []
    real_preview_builder = parser_cli.build_postgresql_persistence_preview

    def fake_preview_builder(persistence_input):
        calls.append(persistence_input)
        return real_preview_builder(persistence_input)

    monkeypatch.setattr(
        parser_cli,
        "build_postgresql_persistence_preview",
        fake_preview_builder,
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
            "--include-postgresql-preview",
        ],
    )

    capsys.readouterr()
    assert exit_code == 0
    assert len(calls) == 1


def test_local_dry_run_cli_postgresql_preview_non_ready_output_is_safe(
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
            "--output-format",
            "json",
            "--include-postgresql-preview",
        ],
    )

    captured = capsys.readouterr()
    postgresql_preview = json.loads(captured.out)["postgresql_persistence_preview"]
    assert exit_code == 1
    assert postgresql_preview["status"] == "no_records"
    assert postgresql_preview["target_table"] is None
    assert postgresql_preview["sql"] is None
    assert postgresql_preview["parameter_rows"] == []
    assert postgresql_preview["issues"][0]["code"] == (
        "POSTGRESQL_PREVIEW_PERSISTENCE_INPUT_NOT_READY"
    )


def test_local_dry_run_cli_postgresql_repository_remains_unsupported(
    tmp_path: Path,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )
    dry_run_result = parser_cli.run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint=None,
    )

    result = PostgreSQLPersistenceRepository().persist(
        dry_run_result.persistence_input,
    )

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.issues[0].code == "POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED"


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


def test_validate_ingestion_config_reports_ready_without_connecting(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive_root = tmp_path / "archive"
    config_path = tmp_path / "ingestion.json"
    config_path.write_text(
        json.dumps(
            {
                "archive_root": str(archive_root),
                "enabled_source_families": ["ghg_protocol"],
                "initial_year": 2024,
                "cycle": {"interval_seconds": 0, "max_cycles": 1},
            },
        ),
        encoding="utf-8",
    )

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("validation must not connect to a database")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_HOST", "localhost")
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_PORT", "5432")
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_DATABASE", "carbonops")
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_USERNAME", "carbonops")
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_PASSWORD", "secret-value")
    monkeypatch.setenv("CARBONOPS_POSTGRESQL_APPLICATION_NAME", "carbonops-test")

    exit_code = parser_cli.main(
        ["validate-ingestion-config", "--config", str(config_path)],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=ready" in captured.out
    assert "postgresql_config_status=ready" in captured.out
    assert "enabled_source_families=ghg_protocol" in captured.out
    assert "postgresql_password_configured=True" in captured.out
    assert "secret-value" not in captured.out


def test_validate_ingestion_config_reports_missing_db_env(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "ingestion.json"
    config_path.write_text(
        json.dumps({"archive_root": str(tmp_path / "archive")}),
        encoding="utf-8",
    )
    for env_name in (
        "CARBONOPS_POSTGRESQL_HOST",
        "CARBONOPS_POSTGRESQL_PORT",
        "CARBONOPS_POSTGRESQL_DATABASE",
        "CARBONOPS_POSTGRESQL_USERNAME",
        "CARBONOPS_POSTGRESQL_PASSWORD",
        "CARBONOPS_POSTGRESQL_APPLICATION_NAME",
    ):
        monkeypatch.delenv(env_name, raising=False)

    exit_code = parser_cli.main(
        ["validate-ingestion-config", "--config", str(config_path)],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=blocked" in captured.out
    assert "POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST" in captured.out
    assert "POSTGRESQL_RUNTIME_CONFIG_MISSING_PASSWORD" in captured.out


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
            "--include-postgresql-preview",
        ],
    )

    assert exit_code == 0


def test_local_dry_run_cli_does_not_scan_directories() -> None:
    module_source = inspect.getsource(parser_cli).lower()

    assert "source_acquisition" not in module_source
    assert "glob(" not in module_source
    assert "rglob(" not in module_source
    assert "iterdir(" not in module_source
    assert "scandir" not in module_source
    assert "walk(" not in module_source
    assert "psycopg" not in module_source
    assert "asyncpg" not in module_source
    assert "sqlalchemy" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert "execute(" not in module_source
    assert ".execute" not in module_source


def _write_fixture(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "defra_fixture.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path
