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


def _dry_run_descriptors() -> tuple[SourceAcquisitionDescriptor, ...]:
    return (
        SourceAcquisitionDescriptor(
            source_id="beta-source",
            source_family="beta",
            display_name="Beta",
            homepage_url="beta-home",
            acquisition_url="beta.csv",
            expected_format="csv",
            description="fixture",
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="gamma-source",
            source_family="gamma",
            display_name="Gamma",
            homepage_url="gamma-home",
            acquisition_url="gamma.json",
            expected_format="json",
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


def test_dry_run_requires_base_directory() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--dry-run"])

    assert excinfo.value.code == 2


def test_dry_run_text_output_includes_source_ids_and_local_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _dry_run_descriptors)

    exit_code = cli.main(["run", "--dry-run", "--base-directory", str(tmp_path)])

    captured = capsys.readouterr()
    output_lines = [line.strip() for line in captured.out.splitlines() if line.strip()]
    assert exit_code == 0
    assert output_lines == [
        f"source_id=beta-source local_path={tmp_path / 'beta-source.csv'}",
        f"source_id=gamma-source local_path={tmp_path / 'gamma-source.json'}",
    ]


def test_dry_run_json_output_is_deterministic_and_ordered(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _dry_run_descriptors)

    first_exit = cli.main(
        ["run", "--dry-run", "--base-directory", str(tmp_path), "--output-format", "json"]
    )
    first_output = capsys.readouterr().out

    second_exit = cli.main(
        ["run", "--dry-run", "--base-directory", str(tmp_path), "--output-format", "json"]
    )
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert second_exit == 0
    assert first_output == second_output

    payload = json.loads(first_output)
    assert payload == {
        "dry_run": True,
        "targets": [
            {
                "source_id": "beta-source",
                "source_family": "beta",
                "expected_format": "csv",
                "local_path": str(tmp_path / "beta-source.csv"),
            },
            {
                "source_id": "gamma-source",
                "source_family": "gamma",
                "expected_format": "json",
                "local_path": str(tmp_path / "gamma-source.json"),
            },
        ],
    }


def test_dry_run_does_not_write_files_or_directories(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _dry_run_descriptors)

    base_directory = tmp_path / "planned"
    exit_code = cli.main(["run", "--dry-run", "--base-directory", str(base_directory)])

    assert exit_code == 0
    assert not base_directory.exists()


def test_dry_run_rejects_manifest_path(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "run",
                "--dry-run",
                "--base-directory",
                str(tmp_path),
                "--manifest-path",
                str(tmp_path / "manifest.json"),
            ]
        )

    assert excinfo.value.code == 2


def test_dry_run_rejects_persist_content(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--dry-run", "--base-directory", str(tmp_path), "--persist-content"])

    assert excinfo.value.code == 2


def test_dry_run_rejects_timeout_seconds(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "run",
                "--dry-run",
                "--base-directory",
                str(tmp_path),
                "--timeout-seconds",
                "4.0",
            ]
        )

    assert excinfo.value.code == 2


def test_dry_run_does_not_instantiate_http_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(cli, "create_default_source_acquisition_registry", _dry_run_descriptors)

    def _fail_transport(*args: object, **kwargs: object) -> object:
        raise AssertionError("HTTP transport should not be instantiated in dry-run mode.")

    monkeypatch.setattr(cli, "StandardLibraryHttpAcquisitionTransport", _fail_transport)

    exit_code = cli.main(
        ["run", "--dry-run", "--base-directory", str(tmp_path), "--client", "http"]
    )

    assert exit_code == 0
