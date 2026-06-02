"""Structured ingestion runtime payload builders.

These helpers produce machine-readable summaries for the configured ingestion
runner while keeping stdout formatting owned by the runner itself.
"""

from __future__ import annotations

from typing import Mapping

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text


def build_configured_runner_summary_payload(result: object) -> dict[str, object]:
    """Build a sanitized JSON-ready summary for a configured runner result."""

    return {
        "status": _status_value(getattr(result, "status", None)),
        "schema_created_table_names": list(
            getattr(result, "schema_created_table_names", ()),
        ),
        "schema_missing_table_names": list(
            getattr(result, "schema_missing_table_names", ()),
        ),
        "cycles": [
            build_configured_cycle_summary_payload(cycle)
            for cycle in getattr(result, "cycles", ())
        ],
    }


def build_configured_cycle_summary_payload(cycle: object) -> dict[str, object]:
    """Build a sanitized JSON-ready summary for one configured cycle."""

    result = getattr(cycle, "result")
    summary = getattr(result, "summary")
    return {
        "cycle_number": getattr(cycle, "cycle_number"),
        "run_id": redact_sensitive_text(str(getattr(cycle, "run_id"))),
        "status": _status_value(getattr(result, "status", None)),
        "summary": {
            "completed_family_count": getattr(summary, "completed_family_count", 0),
            "no_available_source_year_count": getattr(
                summary,
                "no_available_source_year_count",
                0,
            ),
            "failed_family_count": getattr(summary, "failed_family_count", 0),
            "parsed_rows": getattr(summary, "parsed_row_count", 0),
            "inserted": getattr(summary, "inserted_count", 0),
            "skipped_duplicates": getattr(summary, "skipped_duplicate_count", 0),
        },
        "sources": [
            _source_family_payload(family)
            for family in getattr(result, "family_results", ())
        ],
        "issues": _deduplicated_issue_payloads(result),
    }


def _deduplicated_issue_payloads(result: object) -> list[dict[str, object]]:
    """Build sanitized issue payloads without duplicating flattened failures."""

    issues: list[dict[str, object]] = []
    seen: set[tuple[object, object, object, object]] = set()

    def append_issue(issue: object) -> None:
        payload = sanitize_issue_payload(issue)
        key = (
            payload.get("source_family"),
            payload.get("stage"),
            payload.get("code"),
            payload.get("message"),
        )
        if key in seen:
            return
        seen.add(key)
        issues.append(payload)

    for family in getattr(result, "family_results", ()):
        for issue in getattr(family, "failures", ()):
            append_issue(issue)

    for issue in getattr(result, "failures", ()):
        append_issue(issue)

    return issues


def sanitize_issue_payload(issue: object | Mapping[str, object]) -> dict[str, object]:
    """Build a sanitized JSON-ready issue payload."""

    return {
        "source_family": _attr_or_item(issue, "source_family"),
        "stage": _attr_or_item(issue, "stage"),
        "code": _attr_or_item(issue, "code"),
        "message": redact_sensitive_text(str(_attr_or_item(issue, "message") or "")),
    }


def _source_family_payload(family: object) -> dict[str, object]:
    year_state = getattr(family, "year_state")
    insert_summary = getattr(family, "insert_summary", None)
    return {
        "source_family": getattr(family, "source_family"),
        "target_year": getattr(year_state, "target_year"),
        "latest_year": getattr(year_state, "latest_year"),
        "status": _status_value(getattr(family, "status", None)),
        "download_status": _download_status_value(
            getattr(family, "download_result", None),
        ),
        "parse_status": _parse_status_value(family),
        "parsed_rows": getattr(family, "parsed_row_count", 0),
        "master_inserted": getattr(insert_summary, "master_inserted", 0),
        "master_skipped": getattr(insert_summary, "master_skipped", 0),
        "detail_inserted": getattr(insert_summary, "detail_inserted", 0),
        "detail_skipped": getattr(insert_summary, "detail_skipped", 0),
    }


def _download_status_value(download_result: object | None) -> str:
    if download_result is None:
        return "not_run"
    return _status_value(getattr(download_result, "status", "unknown"))


def _parse_status_value(family: object) -> str:
    if getattr(family, "parsed_row_count", 0) > 0:
        return "parsed"
    failures = tuple(getattr(family, "failures", ()))
    if any(getattr(failure, "stage", "") == "parser" for failure in failures):
        return "failed"
    download_result = getattr(family, "download_result", None)
    if (
        download_result is None
        or _download_status_value(download_result) != "downloaded"
    ):
        return "not_run"
    return "no_rows"


def _status_value(status: object) -> str:
    return str(getattr(status, "value", status))


def _attr_or_item(value: object | Mapping[str, object], key: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


__all__ = (
    "build_configured_cycle_summary_payload",
    "build_configured_runner_summary_payload",
    "sanitize_issue_payload",
)
