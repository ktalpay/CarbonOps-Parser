"""Tests for source acquisition CLI run modes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from carbonfactor_parser.source_acquisition import cli
from carbonfactor_parser.source_acquisition.http_client import HttpAcquisitionTransportResponse
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


def _http_descriptors() -> tuple[SourceAcquisitionDescriptor, ...]:
    return (
        SourceAcquisitionDescriptor(
            source_id="alpha",
            source_family="alpha",
            display_name="Alpha",
            homepage_url="alpha-home",
            acquisition_url="alpha.csv",
            expected_format="csv",
            description="fixture",
            enabled=True,
        ),
    )


def test_default_run_uses_noop_behavior(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "acquired_count=0" in captured.out
    assert "failed_count=0" in captured.out
    assert "skipped_count=3" in captured.out


def test_run_with_explicit_noop_matches_default(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["run", "--client", "noop"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "acquired_count=0" in captured.out
    assert "failed_count=0" in captured.out
    assert "skipped_count=3" in captured.out


def test_run_http_mode_uses_http_client_without_persistence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _http_descriptors)

    calls: list[str] = []

    class FakeTransport:
        def __init__(self, timeout_seconds: float | None = None) -> None:
            self.timeout_seconds = timeout_seconds

        def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
            calls.append(acquisition_url)
            return HttpAcquisitionTransportResponse(status_code=200, content=b"a,b\n1,2\n")

    monkeypatch.setattr(cli, "StandardLibraryHttpAcquisitionTransport", FakeTransport)

    exit_code = cli.main(["run", "--client", "http"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == ["alpha.csv"]
    assert "acquired_count=1" in captured.out
    assert "failed_count=0" in captured.out
    assert "skipped_count=0" in captured.out
    assert not list(tmp_path.rglob("*"))


def test_run_http_persist_requires_base_directory() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--client", "http", "--persist-content"])

    assert excinfo.value.code == 2


def test_run_http_persist_writes_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _http_descriptors)

    class FakeTransport:
        def __init__(self, timeout_seconds: float | None = None) -> None:
            self.timeout_seconds = timeout_seconds

        def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
            return HttpAcquisitionTransportResponse(status_code=200, content=b"x,y\n3,4\n")

    monkeypatch.setattr(cli, "StandardLibraryHttpAcquisitionTransport", FakeTransport)

    exit_code = cli.main(
        [
            "run",
            "--client",
            "http",
            "--persist-content",
            "--base-directory",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    persisted_file = tmp_path / "alpha.csv"
    assert persisted_file.exists()
    assert persisted_file.read_bytes() == b"x,y\n3,4\n"


def test_run_noop_with_persist_content_fails_clearly() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--client", "noop", "--persist-content"])

    assert excinfo.value.code == 2


def test_run_noop_with_base_directory_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--client", "noop", "--base-directory", str(tmp_path)])

    assert excinfo.value.code == 2


def test_run_noop_with_timeout_fails_clearly() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--client", "noop", "--timeout-seconds", "2.0"])

    assert excinfo.value.code == 2


def test_run_http_timeout_is_forwarded_to_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _http_descriptors)

    captured_timeout: list[float | None] = []

    class FakeTransport:
        def __init__(self, timeout_seconds: float | None = None) -> None:
            captured_timeout.append(timeout_seconds)

        def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
            return HttpAcquisitionTransportResponse(status_code=200, content=b"n,m\n7,8\n")

    monkeypatch.setattr(cli, "StandardLibraryHttpAcquisitionTransport", FakeTransport)

    exit_code = cli.main(["run", "--client", "http", "--timeout-seconds", "3.5"])

    assert exit_code == 0
    assert captured_timeout == [3.5]


def test_run_http_json_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _http_descriptors)

    class FakeTransport:
        def __init__(self, timeout_seconds: float | None = None) -> None:
            self.timeout_seconds = timeout_seconds

        def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
            return HttpAcquisitionTransportResponse(status_code=200, content=b"q,r\n5,6\n")

    monkeypatch.setattr(cli, "StandardLibraryHttpAcquisitionTransport", FakeTransport)

    exit_code = cli.main(["run", "--client", "http", "--output-format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["acquired_count"] == 1
    assert payload["failed_count"] == 0
    assert payload["skipped_count"] == 0
    assert payload["results"][0]["status"] == "acquired"
