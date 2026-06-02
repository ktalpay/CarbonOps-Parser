"""Centralized redaction helpers for operational diagnostics.

The parser emits local runtime diagnostics for worker operation. This module is a
small safety boundary for those messages: it removes common credential shapes
before text is printed or serialized. It is not intended to be a complete DLP
system.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

_REDACTED_VALUE = "***"
_SENSITIVE_KEYS = frozenset(
    (
        "password",
        "passwd",
        "pwd",
        "token",
        "secret",
        "key",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "private_key",
        "privatekey",
        "dsn",
        "connection_string",
        "connectionstring",
        "connection_uri",
        "connectionuri",
        "database_url",
        "databaseurl",
    )
)
_SENSITIVE_COMPACT_KEYS = frozenset(key.replace("_", "") for key in _SENSITIVE_KEYS)
_URL_PATTERN = re.compile(r"(?P<url>[a-z][a-z0-9+.-]*://[^\s'\"<>]+)", re.I)
_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?<![\w-])(?P<prefix>(?P<key>[a-z][a-z0-9_-]*)\s*[:=]\s*)"
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

    query = _redact_query(parsed.query) if parsed.query else parsed.query

    return urlunsplit((parsed.scheme, netloc, parsed.path, query, parsed.fragment))


def _redact_query(query: str) -> str:
    redacted_parts = []
    for part in query.split("&"):
        key, separator, _value = part.partition("=")
        if separator and _is_sensitive_key(key):
            redacted_parts.append(f"{key}={_REDACTED_VALUE}")
        else:
            redacted_parts.append(part)
    return "&".join(redacted_parts)


def _redact_assignment_match(match: re.Match[str]) -> str:
    if not _is_sensitive_key(match.group("key")):
        return match.group(0)
    quote = match.group("quote") or ""
    return f"{match.group('prefix')}{quote}{_REDACTED_VALUE}{quote}"


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return (
        normalized in _SENSITIVE_KEYS
        or normalized.replace("_", "") in _SENSITIVE_COMPACT_KEYS
    )


__all__ = ("redact_sensitive_text",)
