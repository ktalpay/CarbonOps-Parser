import json
import sqlite3
import urllib.request
from pathlib import Path

import pytest

import carbonfactor_parser.cli as parser_cli


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPOSITORY_ROOT / "examples" / "fixtures" / "defra_desnz_minimal.csv"


def test_local_dry_run_fixture_quickstart_cli_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("fixture quickstart must not connect to a database")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("fixture quickstart must not perform network calls")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    exit_code = parser_cli.main(
        [
            "local-dry-run",
            "--local-path",
            str(FIXTURE_PATH),
            "--source-family",
            "defra_desnz",
            "--source-id",
            "defra-desnz-minimal-fixture",
            "--content-type",
            "text/csv",
            "--format-hint",
            "csv",
            "--output-format",
            "json",
        ],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "success"
    assert payload["parsed_record_count"] == 2
    assert payload["normalization_record_count"] == 2
    assert payload["persistence_input_record_count"] == 2
    assert payload["ddl_preview_present"] is True
    assert payload["source_family"] == "defra_desnz"
    assert payload["source_id"] == "defra-desnz-minimal-fixture"
    assert payload["issues"] == []
