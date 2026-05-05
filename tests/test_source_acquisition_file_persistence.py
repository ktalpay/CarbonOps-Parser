from pathlib import Path

import pytest

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex
from carbonfactor_parser.source_acquisition.http_client import (
    HttpAcquisitionTransportResponse,
    HttpSourceAcquisitionClient,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.targets import plan_source_acquisition_target


def _build_descriptor() -> SourceAcquisitionDescriptor:
    return SourceAcquisitionDescriptor(
        source_id="example_source",
        source_family="example_family",
        display_name="Example Source",
        homepage_url="discovery://example",
        acquisition_url="discovery://example/source.csv",
        expected_format="csv",
        description="Example descriptor",
        enabled=True,
    )


def test_persist_content_false_keeps_metadata_only_behavior(tmp_path: Path) -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=200, content=b"x,y\n1,2\n")

    result = HttpSourceAcquisitionClient(
        fake_transport,
        base_directory=tmp_path,
        persist_content=False,
    ).acquire(_build_descriptor())

    assert result.status == "acquired"
    assert result.local_path is None
    assert not any(tmp_path.iterdir())


def test_persist_content_true_writes_to_planned_target_and_sets_local_path(tmp_path: Path) -> None:
    content = b"a,b\n3,4\n"

    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=200, content=content)

    descriptor = _build_descriptor()
    target = plan_source_acquisition_target(descriptor, tmp_path / "acquired")

    result = HttpSourceAcquisitionClient(
        fake_transport,
        base_directory=tmp_path / "acquired",
        persist_content=True,
    ).acquire(descriptor)

    assert result.status == "acquired"
    assert result.local_path == target.local_path
    assert target.local_path.read_bytes() == content
    assert result.checksum_sha256 == compute_sha256_hex(content)


def test_persist_content_true_overwrites_existing_file(tmp_path: Path) -> None:
    descriptor = _build_descriptor()
    target = plan_source_acquisition_target(descriptor, tmp_path)
    target.local_path.parent.mkdir(parents=True, exist_ok=True)
    target.local_path.write_bytes(b"old")

    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=200, content=b"new")

    result = HttpSourceAcquisitionClient(
        fake_transport,
        base_directory=tmp_path,
        persist_content=True,
    ).acquire(descriptor)

    assert result.local_path == target.local_path
    assert target.local_path.read_bytes() == b"new"


def test_non_2xx_does_not_write_files(tmp_path: Path) -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=404, content=b"missing")

    result = HttpSourceAcquisitionClient(
        fake_transport,
        base_directory=tmp_path,
        persist_content=True,
    ).acquire(_build_descriptor())

    assert result.status == "failed"
    assert result.local_path is None
    assert result.checksum_sha256 is None
    assert not any(tmp_path.iterdir())


def test_transport_exception_does_not_write_files(tmp_path: Path) -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        raise RuntimeError("offline failure")

    result = HttpSourceAcquisitionClient(
        fake_transport,
        base_directory=tmp_path,
        persist_content=True,
    ).acquire(_build_descriptor())

    assert result.status == "failed"
    assert result.local_path is None
    assert result.checksum_sha256 is None
    assert not any(tmp_path.iterdir())


def test_persist_content_true_requires_base_directory() -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=200, content=b"ok")

    with pytest.raises(ValueError, match="base_directory"):
        HttpSourceAcquisitionClient(fake_transport, persist_content=True)


def test_write_acquired_content_public_export_is_importable() -> None:
    assert callable(source_acquisition.write_acquired_content)
