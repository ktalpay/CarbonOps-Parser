"""Structured Phase 1 observability helpers with safe diagnostic output."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import logging
import re
from typing import Any, Mapping

from carbonfactor_parser.persistence.postgresql_options import (
    PostgreSQLPersistenceOptions,
)


PHASE1_OPERATIONAL_LOGGER_NAME = "carbonfactor_parser.phase1"
REDACTED = "<redacted>"

_CHECKSUM_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
_USERINFO_URI_PATTERN = re.compile(r"//[^/\s:@]+:[^@\s/]+@")
_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|dsn|connection_string)=([^\s;,]+)",
)
_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "credential",
    "dsn",
    "connection_string",
    "connection_uri",
    "database_url",
)
_SENSITIVE_RUNTIME_OPTION_FIELDS = frozenset(
    {
        "host",
        "database",
        "username",
        "application_name",
        "dsn",
        "connection_string",
        "connection_uri",
        "database_url",
    }
)


def get_phase1_operational_logger() -> logging.Logger:
    """Return the shared Phase 1 operational logger."""

    return logging.getLogger(PHASE1_OPERATIONAL_LOGGER_NAME)


def emit_phase1_operational_event(
    event_name: str,
    payload: Mapping[str, Any],
    *,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> dict[str, Any]:
    """Emit one deterministic JSON operational event and return its payload."""

    safe_payload = redact_diagnostic_value("payload", payload)
    event = _stable_mapping(
        {
            "event": event_name,
            **safe_payload,
        }
    )
    active_logger = logger or get_phase1_operational_logger()
    active_logger.log(
        level,
        json.dumps(event, sort_keys=True, separators=(",", ":")),
    )
    return event


def summarize_postgresql_options_for_diagnostics(
    options: PostgreSQLPersistenceOptions,
) -> dict[str, Any]:
    """Return PostgreSQL option metadata without runtime-sensitive values."""

    return {
        "application_name": REDACTED if options.application_name is not None else None,
        "connect_timeout_seconds": options.connect_timeout_seconds,
        "database": REDACTED,
        "host": REDACTED,
        "password_set": options.password_set,
        "port": options.port,
        "ssl_mode": options.ssl_mode,
        "username": REDACTED,
    }


def summarize_phase1_orchestrator_request(request: Any) -> dict[str, Any]:
    """Return correlation-safe request metadata for Phase 1 diagnostics."""

    return {
        "correlation_id": _safe_text(getattr(request, "correlation_id", None)),
        "execution_mode": _enum_value(getattr(request, "execution_mode", None)),
        "max_degree_of_parallelism": getattr(request, "max_parallelism", None),
        "run_id": _safe_text(getattr(request, "run_id", None)),
        "source_families": tuple(getattr(request, "source_families", ())),
    }


def summarize_phase1_family_result_for_diagnostics(
    family_result: Any,
    *,
    run_id: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Return deterministic per-source-family operational counts and IDs."""

    acquisition_result = getattr(family_result, "acquisition_result", None)
    parser_run_result = getattr(family_result, "parser_run_result", None)

    return {
        "correlation_id": _safe_text(correlation_id),
        "documents": _document_summaries(acquisition_result, run_id),
        "failures": _failure_summaries(getattr(family_result, "failures", ())),
        "parser": {
            "accepted_row_count": _nested_attr(
                parser_run_result,
                "summary",
                "row_count",
                0,
            ),
            "failure_count": _nested_attr(
                parser_run_result,
                "summary",
                "error_count",
                0,
            ),
            "result_status": _enum_value(getattr(parser_run_result, "status", None)),
            "run_id": _safe_text(getattr(parser_run_result, "run_id", None)),
            "validation_issue_count": _nested_attr(
                parser_run_result,
                "summary",
                "issue_count",
                0,
            ),
        },
        "persistence": {
            "parsed_factor_detail_count": getattr(
                family_result,
                "persisted_detail_count",
                0,
            ),
            "parsed_factor_master_count": getattr(
                family_result,
                "persisted_master_count",
                0,
            ),
            "parser_run_count": getattr(family_result, "persisted_parser_run_count", 0),
            "source_document_count": getattr(
                family_result,
                "persisted_source_document_count",
                0,
            ),
            "source_run_count": getattr(family_result, "persisted_source_run_count", 0),
        },
        "run_id": _safe_text(run_id),
        "source_family": getattr(family_result, "source_family", None),
        "source_key": _source_key(family_result),
        "status": _enum_value(getattr(family_result, "status", None)),
    }


def summarize_phase1_orchestrator_result_for_diagnostics(result: Any) -> dict[str, Any]:
    """Return deterministic run-level operational counts and failures."""

    request = getattr(result, "request", None)
    summary = getattr(result, "summary", None)
    return {
        "correlation_id": _safe_text(getattr(request, "correlation_id", None)),
        "failures": _failure_summaries(getattr(result, "failures", ())),
        "run_id": _safe_text(getattr(request, "run_id", None)),
        "selected_source_families": tuple(
            getattr(result, "selected_source_families", ()),
        ),
        "source_family_statuses": tuple(
            {
                "source_family": getattr(family_result, "source_family", None),
                "status": _enum_value(getattr(family_result, "status", None)),
            }
            for family_result in getattr(result, "family_results", ())
        ),
        "status": _enum_value(getattr(result, "status", None)),
        "summary": _dataclass_or_mapping(summary),
    }


def redact_diagnostic_value(field_name: str, value: Any) -> Any:
    """Redact sensitive diagnostic values while preserving deterministic shape."""

    if _is_sensitive_field(field_name):
        return REDACTED if value is not None else None
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, Mapping):
        return {
            str(key): redact_diagnostic_value(str(key), item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple):
        return tuple(redact_diagnostic_value(field_name, item) for item in value)
    if isinstance(value, list):
        return tuple(redact_diagnostic_value(field_name, item) for item in value)
    return value


def _document_summaries(
    acquisition_result: Any,
    run_id: str,
) -> tuple[dict[str, Any], ...]:
    if acquisition_result is None:
        return ()
    return tuple(
        {
            "checksum_sha256": _safe_checksum(
                getattr(artifact, "checksum_sha256", None),
            ),
            "document_id": _safe_text(getattr(artifact, "artifact_id", None)),
            "source_family": getattr(artifact, "source_family", None),
            "source_key": getattr(artifact, "source_key", None),
        }
        for artifact in getattr(acquisition_result, "artifacts", ())
    )


def _failure_summaries(failures: Any) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "code": getattr(failure, "code", None),
            "field_name": getattr(failure, "field_name", None),
            "message": _safe_text(getattr(failure, "message", None)),
            "severity": getattr(failure, "severity", None),
            "source_family": getattr(failure, "source_family", None),
            "source_key": _failure_source_key(failure),
            "stage": getattr(failure, "stage", None),
        }
        for failure in failures
    )


def _dataclass_or_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if is_dataclass(value):
        return _stable_mapping(asdict(value))
    if isinstance(value, Mapping):
        return _stable_mapping(value)
    return {}


def _stable_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): _stable_value(item)
        for key, item in sorted(value.items(), key=lambda item: str(item[0]))
    }


def _stable_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _stable_mapping(value)
    if is_dataclass(value):
        return _stable_mapping(asdict(value))
    if isinstance(value, list):
        return tuple(_stable_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_stable_value(item) for item in value)
    if hasattr(value, "value"):
        return value.value
    return value


def _safe_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    without_userinfo = _USERINFO_URI_PATTERN.sub(f"//{REDACTED}@", value)
    return _SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}={REDACTED}",
        without_userinfo,
    )


def _safe_checksum(value: Any) -> str | None:
    if not isinstance(value, str) or not _CHECKSUM_PATTERN.match(value):
        return None
    return value.lower()


def _is_sensitive_field(field_name: str) -> bool:
    normalized = field_name.strip().lower()
    return (
        normalized in _SENSITIVE_RUNTIME_OPTION_FIELDS
        or any(part in normalized for part in _SENSITIVE_KEY_PARTS)
    )


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _nested_attr(value: Any, first: str, second: str, default: Any) -> Any:
    nested = getattr(value, first, None)
    return getattr(nested, second, default)


def _source_key(family_result: Any) -> Any:
    source_key = getattr(family_result, "source_key", None)
    if source_key is not None:
        return source_key
    acquisition_result = getattr(family_result, "acquisition_result", None)
    if acquisition_result is not None:
        return getattr(acquisition_result, "source_key", None)
    return getattr(family_result, "source_family", None)


def _failure_source_key(failure: Any) -> Any:
    source_key = getattr(failure, "source_key", None)
    if source_key is not None:
        return source_key
    return getattr(failure, "source_family", None)


__all__ = (
    "PHASE1_OPERATIONAL_LOGGER_NAME",
    "REDACTED",
    "emit_phase1_operational_event",
    "get_phase1_operational_logger",
    "redact_diagnostic_value",
    "summarize_phase1_family_result_for_diagnostics",
    "summarize_phase1_orchestrator_request",
    "summarize_phase1_orchestrator_result_for_diagnostics",
    "summarize_postgresql_options_for_diagnostics",
)
