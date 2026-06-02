"""Artifact transport helpers for configured source-year artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def build_configured_artifact_transport(
    allow_live_source_access: bool,
) -> Callable[[str], bytes]:
    """Build a source artifact transport with the configured live-access policy."""

    def transport(uri: str) -> bytes:
        return _configured_artifact_transport(
            uri,
            allow_live_source_access=allow_live_source_access,
        )

    return transport


def _configured_artifact_transport(
    uri: str,
    *,
    allow_live_source_access: bool = False,
) -> bytes:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(parsed.path).read_bytes()
    if parsed.scheme in {"", "local"}:
        return Path(parsed.path if parsed.scheme == "local" else uri).read_bytes()
    if parsed.scheme == "https":
        if not allow_live_source_access:
            raise ValueError(
                "Live HTTPS source access requires explicit real-source smoke opt-in.",
            )
        request = Request(uri, headers={"User-Agent": "carbonops-parser/0.1"})
        with urlopen(request, timeout=60) as response:  # noqa: S310
            return bytes(response.read())
    raise ValueError("Configured artifacts must use file, local path, or HTTPS URI.")


__all__ = ("build_configured_artifact_transport",)
