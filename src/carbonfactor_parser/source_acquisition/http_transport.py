"""Standard-library HTTP transport for source acquisition."""

from __future__ import annotations

from urllib.error import HTTPError
from urllib.request import urlopen

from carbonfactor_parser.source_acquisition.http_client import (
    HttpAcquisitionTransportResponse,
)


class StandardLibraryHttpAcquisitionTransport:
    """Callable HTTP transport backed by urllib.request.urlopen."""

    def __init__(self, timeout_seconds: float | None = None) -> None:
        self._timeout_seconds = timeout_seconds

    def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
        if not acquisition_url:
            raise ValueError("acquisition_url must not be empty.")

        try:
            with urlopen(acquisition_url, timeout=self._timeout_seconds) as response:
                return HttpAcquisitionTransportResponse(
                    status_code=response.status,
                    content=response.read(),
                    content_type=response.headers.get_content_type(),
                    content_length=_parse_content_length(
                        response.headers.get("Content-Length"),
                    ),
                    final_url=response.geturl(),
                )
        except HTTPError as error:
            error_body = error.read()
            return HttpAcquisitionTransportResponse(
                status_code=error.code,
                content=error_body,
                content_type=error.headers.get_content_type() if error.headers else None,
                content_length=_parse_content_length(
                    error.headers.get("Content-Length") if error.headers else None,
                ),
                final_url=error.geturl(),
            )


def _parse_content_length(raw_content_length: str | None) -> int | None:
    if raw_content_length is None:
        return None

    stripped_length = raw_content_length.strip()
    if not stripped_length:
        return None

    try:
        return int(stripped_length)
    except ValueError:
        return None
