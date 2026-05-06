from __future__ import annotations

import json

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.client import (
    NoopSourceAcquisitionClient,
    SourceAcquisitionClient,
    SourceAcquisitionResult,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.run import (
    SourceAcquisitionRunResult,
    run_source_acquisition,
)


class FakeSourceAcquisitionClient(SourceAcquisitionClient):
    def __init__(self, results_by_id: dict[str, SourceAcquisitionResult]) -> None:
        self._results_by_id = results_by_id

    def acquire(self, descriptor: SourceAcquisitionDescriptor) -> SourceAcquisitionResult:
        return self._results_by_id[descriptor.source_id]


def _descriptor(source_id: str) -> SourceAcquisitionDescriptor:
    return SourceAcquisitionDescriptor(
        source_id=source_id,
        source_family="family",
        display_name=f"Display {source_id}",
        homepage_url=f"https://example.invalid/{source_id}/home",
        acquisition_url=f"https://example.invalid/{source_id}/acquire",
        expected_format="csv",
        description="test descriptor",
    )


def _result(source_id: str, status: str) -> SourceAcquisitionResult:
    return SourceAcquisitionResult(
        source_id=source_id,
        source_family="family",
        status=status,
        acquisition_url=f"https://example.invalid/{source_id}/acquire",
        message=f"{status} message",
    )


def test_run_source_acquisition_preserves_descriptor_order() -> None:
    descriptors = (_descriptor("b"), _descriptor("a"), _descriptor("c"))
    client = FakeSourceAcquisitionClient(
        {source.source_id: _result(source.source_id, "acquired") for source in descriptors}
    )

    run = run_source_acquisition(descriptors, client)

    assert tuple(result.source_id for result in run.results) == ("b", "a", "c")


def test_run_source_acquisition_counts_acquired_failed_and_skipped() -> None:
    descriptors = (
        _descriptor("acquired"),
        _descriptor("failed"),
        _descriptor("skipped"),
        _descriptor("not_implemented"),
    )
    client = FakeSourceAcquisitionClient(
        {
            "acquired": _result("acquired", "acquired"),
            "failed": _result("failed", "failed"),
            "skipped": _result("skipped", "skipped"),
            "not_implemented": _result("not_implemented", "not_implemented"),
        }
    )

    run = run_source_acquisition(descriptors, client)

    assert run.acquired_count == 1
    assert run.failed_count == 1
    assert run.skipped_count == 2


def test_run_source_acquisition_without_manifest_does_not_write_files(tmp_path) -> None:
    descriptors = (_descriptor("one"),)
    client = FakeSourceAcquisitionClient({"one": _result("one", "acquired")})
    manifest_path = tmp_path / "manifests" / "acquisition.json"

    run = run_source_acquisition(descriptors, client)

    assert run.manifest_path is None
    assert manifest_path.exists() is False


def test_run_source_acquisition_with_manifest_writes_deterministic_json(tmp_path) -> None:
    descriptors = (_descriptor("one"), _descriptor("two"))
    client = FakeSourceAcquisitionClient(
        {
            "one": _result("one", "acquired"),
            "two": _result("two", "failed"),
        }
    )
    manifest_path = tmp_path / "manifests" / "acquisition.json"

    run = run_source_acquisition(descriptors, client, manifest_path=manifest_path)

    assert run.manifest_path == manifest_path
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["source_id"] for item in payload] == ["one", "two"]
    assert [item["status"] for item in payload] == ["acquired", "failed"]


def test_run_source_acquisition_manifest_entries_match_results() -> None:
    descriptors = (_descriptor("one"), _descriptor("two"))
    client = FakeSourceAcquisitionClient(
        {
            "one": _result("one", "acquired"),
            "two": _result("two", "failed"),
        }
    )

    run = run_source_acquisition(descriptors, client)

    assert tuple(entry.source_id for entry in run.manifest_entries) == tuple(
        result.source_id for result in run.results
    )
    assert tuple(entry.status for entry in run.manifest_entries) == tuple(
        result.status for result in run.results
    )


def test_run_source_acquisition_with_noop_client_counts_not_implemented_as_skipped() -> None:
    descriptors = (_descriptor("one"), _descriptor("two"))

    run = run_source_acquisition(descriptors, NoopSourceAcquisitionClient())

    assert run.acquired_count == 0
    assert run.failed_count == 0
    assert run.skipped_count == 2


def test_run_source_acquisition_public_exports_are_importable() -> None:
    assert source_acquisition.SourceAcquisitionRunResult is SourceAcquisitionRunResult
    assert source_acquisition.run_source_acquisition is run_source_acquisition
