from __future__ import annotations

from email.message import Message
from io import BytesIO

import pytest
from urllib.error import HTTPError, URLError

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.http_client import HttpAcquisitionTransportResponse
from carbonfactor_parser.source_acquisition.http_transport import (
    StandardLibraryHttpAcquisitionTransport,
)


class _FakeUrlopenResponse:
    def __init__(
        self,
        *,
        status: int,
        body: bytes,
        content_type: str,
        content_length: str,
        final_url: str,
    ) -> None:
        headers = Message()
        headers["Content-Type"] = content_type
        headers["Content-Length"] = content_length

        self.status = status
        self._body = body
        self.headers = headers
        self._final_url = final_url

    def read(self) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._final_url

    def __enter__(self) -> _FakeUrlopenResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None


def test_standard_library_transport_success_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(url: str, timeout: float | None = None) -> _FakeUrlopenResponse:
        captured["url"] = url
        captured["timeout"] = timeout
        return _FakeUrlopenResponse(
            status=200,
            body=b"{\"ok\":true}",
            content_type="application/json",
            content_length="11",
            final_url="discovery://example.test/final",
        )

    monkeypatch.setattr("carbonfactor_parser.source_acquisition.http_transport.urlopen", fake_urlopen)

    transport = StandardLibraryHttpAcquisitionTransport(timeout_seconds=5.0)
    response = transport("discovery://example.test/data")

    assert isinstance(response, HttpAcquisitionTransportResponse)
    assert response.status_code == 200
    assert response.content == b"{\"ok\":true}"
    assert response.content_type == "application/json"
    assert response.content_length == 11
    assert response.final_url == "discovery://example.test/final"
    assert captured == {"url": "discovery://example.test/data", "timeout": 5.0}


def test_standard_library_transport_empty_url_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        StandardLibraryHttpAcquisitionTransport()("")


def test_standard_library_transport_http_error_returns_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = Message()
    headers["Content-Type"] = "text/plain"
    headers["Content-Length"] = "9"

    def fake_urlopen(_: str, timeout: float | None = None) -> _FakeUrlopenResponse:
        del timeout
        raise HTTPError(
            url="discovery://example.test/missing",
            code=404,
            msg="Not Found",
            hdrs=headers,
            fp=BytesIO(b"not found"),
        )

    monkeypatch.setattr("carbonfactor_parser.source_acquisition.http_transport.urlopen", fake_urlopen)

    response = StandardLibraryHttpAcquisitionTransport()("discovery://example.test/missing")

    assert response.status_code == 404
    assert response.content == b"not found"
    assert response.content_type == "text/plain"
    assert response.content_length == 9
    assert response.final_url == "discovery://example.test/missing"


def test_standard_library_transport_url_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(_: str, timeout: float | None = None) -> _FakeUrlopenResponse:
        del timeout
        raise URLError("offline")

    monkeypatch.setattr("carbonfactor_parser.source_acquisition.http_transport.urlopen", fake_urlopen)

    with pytest.raises(URLError):
        StandardLibraryHttpAcquisitionTransport()("discovery://example.test/offline")


def test_standard_library_transport_public_export_is_importable() -> None:
    assert (
        source_acquisition.StandardLibraryHttpAcquisitionTransport
        is StandardLibraryHttpAcquisitionTransport
    )
