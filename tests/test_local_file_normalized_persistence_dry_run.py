import inspect
import sqlite3
import urllib.request
from pathlib import Path

import pytest

import carbonfactor_parser.pipeline.local_dry_run as local_dry_run_module
from carbonfactor_parser.parsers import ParserExecutionResultStatus
from carbonfactor_parser.persistence import PersistenceInput
from carbonfactor_parser.pipeline import (
    LocalFilePersistenceDryRunStatus,
    run_local_file_normalized_persistence_dry_run,
)


def test_valid_local_defra_desnz_fixture_produces_success_dry_run(
    tmp_path: Path,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n2,Gas,kWh\n",
    )

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="defra-desnz-fixture",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.SUCCESS
    assert result.is_success is True
    assert result.parser_result is not None
    assert result.parser_result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parser_result.parsed_record_count == 2
    assert result.persistence_input is not None
    assert len(result.persistence_input.records) == 2


def test_dry_run_result_contains_persistence_input(tmp_path: Path) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert isinstance(result.persistence_input, PersistenceInput)
    assert result.persistence_input.source_family == "defra_desnz"
    assert result.persistence_input.source_id == "source-001"
    record = result.persistence_input.records[0]
    assert record.source_family == "defra_desnz"
    assert record.source_id == "source-001"
    assert dict(record.normalized_fields)["factor_name"] == "Electricity"


def test_dry_run_result_contains_ddl_preview_metadata_only(tmp_path: Path) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.ddl_preview is not None
    assert "CREATE TABLE normalized_records" in result.ddl_preview
    assert result.ddl_preview_metadata == {
        "preview_only": True,
        "sql_execution": False,
        "database_connection": False,
        "migration": False,
    }


def test_missing_file_returns_structured_failure_and_stops_before_downstream_steps(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.csv"

    result = run_local_file_normalized_persistence_dry_run(
        local_path=missing_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.FAILED
    assert result.load_result is not None
    assert result.parser_result is None
    assert result.handoff_result is None
    assert result.normalization_input_build_result is None
    assert result.normalization_mapping_result is None
    assert result.persistence_input_build_result is None
    assert result.persistence_input is None
    assert result.ddl_preview is None
    assert result.issues[0].stage == "load"


def test_invalid_parser_content_returns_failure_without_persistence_input(
    tmp_path: Path,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "wrong,header\n1,Electricity\n",
    )

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.FAILED
    assert result.parser_result is not None
    assert result.parser_result.status == ParserExecutionResultStatus.FAILED
    assert result.handoff_result is not None
    assert result.normalization_input_build_result is None
    assert result.normalization_mapping_result is None
    assert result.persistence_input_build_result is None
    assert result.persistence_input is None
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_INVALID_HEADER"


def test_no_record_parser_content_returns_no_records_without_persistence_input(
    tmp_path: Path,
) -> None:
    file_path = _write_fixture(tmp_path, "factor_id,factor_name,unit\n")

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.NO_RECORDS
    assert result.parser_result is not None
    assert result.parser_result.status == ParserExecutionResultStatus.NO_RECORDS
    assert result.persistence_input is None
    assert result.ddl_preview is None


def test_missing_required_normalization_field_returns_failure(
    tmp_path: Path,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n,Electricity,kWh\n",
    )

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.FAILED
    assert result.parser_result is not None
    assert result.parser_result.status == ParserExecutionResultStatus.SUCCESS
    assert result.normalization_input_build_result is not None
    assert result.normalization_mapping_result is not None
    assert result.persistence_input_build_result is None
    assert result.persistence_input is None
    assert result.issues[0].code == "DEFRA_DESNZ_NORMALIZATION_MISSING_RAW_FIELD"
    assert result.issues[0].stage == "normalization_mapping"


def test_dry_run_has_no_database_or_network_behavior(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = _write_fixture(
        tmp_path,
        "factor_id,factor_name,unit\n1,Electricity,kWh\n",
    )

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("dry-run must not connect to a database")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("dry-run must not perform network calls")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    result = run_local_file_normalized_persistence_dry_run(
        local_path=file_path,
        source_family="defra_desnz",
        source_id="source-001",
        content_type="text/csv",
        format_hint="csv",
    )

    assert result.status == LocalFilePersistenceDryRunStatus.SUCCESS


def test_dry_run_module_avoids_database_runtime_imports() -> None:
    module_source = inspect.getsource(local_dry_run_module).lower()

    assert "psycopg" not in module_source
    assert "sqlalchemy" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert ".execute" not in module_source
    assert "urllib" not in module_source


def _write_fixture(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "defra_fixture.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path
