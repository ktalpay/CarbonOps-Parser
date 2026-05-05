from __future__ import annotations

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.client import NoopSourceAcquisitionClient, SourceAcquisitionResult
from carbonfactor_parser.source_acquisition.http_client import (
    HttpAcquisitionTransportResponse,
    HttpSourceAcquisitionClient,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.status import (
    ACQUISITION_FAILED_STATUSES,
    ACQUISITION_KNOWN_STATUSES,
    ACQUISITION_SKIPPED_STATUSES,
    ACQUISITION_STATUS_ACQUIRED,
    ACQUISITION_STATUS_FAILED,
    ACQUISITION_STATUS_NOT_IMPLEMENTED,
    ACQUISITION_STATUS_SKIPPED,
    ACQUISITION_SUCCESS_STATUSES,
    count_acquisition_statuses,
    is_acquired_status,
    is_failed_status,
    is_skipped_status,
)


def _descriptor() -> SourceAcquisitionDescriptor:
    return SourceAcquisitionDescriptor(
        source_id="example_source",
        source_family="example_family",
        display_name="Example Source",
        homepage_url="discovery://example",
        acquisition_url="discovery://example/source",
        expected_format="csv",
        description="Example descriptor",
        enabled=True,
    )


def _result(status: str) -> SourceAcquisitionResult:
    descriptor = _descriptor()
    return SourceAcquisitionResult(
        source_id=descriptor.source_id,
        source_family=descriptor.source_family,
        status=status,
        acquisition_url=descriptor.acquisition_url,
    )


def test_status_constants_preserve_existing_string_values() -> None:
    assert ACQUISITION_STATUS_ACQUIRED == "acquired"
    assert ACQUISITION_STATUS_FAILED == "failed"
    assert ACQUISITION_STATUS_SKIPPED == "skipped"
    assert ACQUISITION_STATUS_NOT_IMPLEMENTED == "not_implemented"


def test_status_collections_are_classified_deterministically() -> None:
    assert ACQUISITION_SUCCESS_STATUSES == frozenset({"acquired"})
    assert ACQUISITION_FAILED_STATUSES == frozenset({"failed"})
    assert ACQUISITION_SKIPPED_STATUSES == frozenset({"skipped", "not_implemented"})
    assert ACQUISITION_KNOWN_STATUSES == frozenset(
        {"acquired", "failed", "skipped", "not_implemented"}
    )


def test_status_predicates_classify_known_and_unknown_values() -> None:
    assert is_acquired_status(ACQUISITION_STATUS_ACQUIRED)
    assert is_failed_status(ACQUISITION_STATUS_FAILED)
    assert is_skipped_status(ACQUISITION_STATUS_SKIPPED)
    assert is_skipped_status(ACQUISITION_STATUS_NOT_IMPLEMENTED)

    assert not is_acquired_status("unknown")
    assert not is_failed_status("unknown")
    assert not is_skipped_status("unknown")


def test_count_acquisition_statuses_matches_run_semantics() -> None:
    acquired_count, failed_count, skipped_count = count_acquisition_statuses(
        (
            _result(ACQUISITION_STATUS_ACQUIRED),
            _result(ACQUISITION_STATUS_FAILED),
            _result(ACQUISITION_STATUS_SKIPPED),
            _result(ACQUISITION_STATUS_NOT_IMPLEMENTED),
            _result("unknown"),
        )
    )

    assert (acquired_count, failed_count, skipped_count) == (1, 1, 2)


def test_noop_client_status_value_is_unchanged() -> None:
    result = NoopSourceAcquisitionClient().acquire(_descriptor())
    assert result.status == ACQUISITION_STATUS_NOT_IMPLEMENTED


def test_http_client_uses_status_constants_for_success_failure_and_exception() -> None:
    success = HttpSourceAcquisitionClient(
        lambda _: HttpAcquisitionTransportResponse(status_code=200, content=b"ok")
    ).acquire(_descriptor())
    assert success.status == ACQUISITION_STATUS_ACQUIRED

    failed = HttpSourceAcquisitionClient(
        lambda _: HttpAcquisitionTransportResponse(status_code=503, content=b"no")
    ).acquire(_descriptor())
    assert failed.status == ACQUISITION_STATUS_FAILED

    def raising_transport(_: str) -> HttpAcquisitionTransportResponse:
        raise RuntimeError("offline")

    exception = HttpSourceAcquisitionClient(raising_transport).acquire(_descriptor())
    assert exception.status == ACQUISITION_STATUS_FAILED


def test_status_helpers_are_publicly_exported() -> None:
    assert source_acquisition.ACQUISITION_STATUS_ACQUIRED == ACQUISITION_STATUS_ACQUIRED
    assert source_acquisition.is_acquired_status is is_acquired_status
    assert source_acquisition.count_acquisition_statuses is count_acquisition_statuses
