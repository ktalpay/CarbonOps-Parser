"""Centralized redaction helpers for operational diagnostics.

The parser emits local runtime diagnostics for worker operation. This module is a
small safety boundary for those messages: it removes common credential shapes
before text is printed or serialized. It is not intended to be a complete DLP
system.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_REDACTED_VALUE = "***"
_SENSITIVE_ASSIGNMENT_KEYS = (
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "key",
    "dsn",
    "connection_string",
)
_SENSITIVE_QUERY_KEYS = frozenset(_SENSITIVE_ASSIGNMENT_KEYS)
_URL_PATTERN = re.compile(r"(?P<url>[a-z][a-z0-9+.-]*://[^\s'\"<>]+)", re.I)
_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?P<prefix>\b(?:password|passwd|pwd|token|secret|key|dsn|connection_string)\b\s*[:=]\s*)"
    r"(?P<quote>['\"]?)"
    r"(?P<value>[^\s,;)}\]\"']+)"
    r"(?P=quote)",
)


def redact_sensitive_text(value: str) -> str:
    """Return ``value`` with common credential-bearing content redacted."""

    text = str(value)
    text = _URL_PATTERN.sub(lambda match: _redact_url_match(match.group("url")), text)
    return _ASSIGNMENT_PATTERN.sub(_redact_assignment_match, text)


def _redact_url_match(url: str) -> str:
    trailing = ""
    while url and url[-1] in ".,;)]}":
        trailing = url[-1] + trailing
        url = url[:-1]
    return _redact_url(url) + trailing


def _redact_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return url

    netloc = parsed.netloc
    if "@" in netloc:
        host_port = netloc.rsplit("@", 1)[1]
        netloc = f"{_REDACTED_VALUE}@{host_port}"

    query = parsed.query
    if query:
        query_pairs = parse_qsl(query, keep_blank_values=True)
        redacted_pairs = [
            (
                key,
                _REDACTED_VALUE
                if key.strip().lower() in _SENSITIVE_QUERY_KEYS
                else val,
            )
            for key, val in query_pairs
        ]
        query = urlencode(redacted_pairs, doseq=True)

    return urlunsplit((parsed.scheme, netloc, parsed.path, query, parsed.fragment))


def _redact_assignment_match(match: re.Match[str]) -> str:
    quote = match.group("quote") or ""
    return f"{match.group('prefix')}{quote}{_REDACTED_VALUE}{quote}"


__all__ = ("redact_sensitive_text",)
