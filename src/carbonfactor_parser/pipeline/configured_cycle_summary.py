"""Configured ingestion cycle summary output helpers."""

from __future__ import annotations

from typing import Callable

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.pipeline.configured_cycle_models import ConfiguredCycleResult


def emit_configured_cycle_summary(
    cycle: ConfiguredCycleResult,
    *,
    emit: Callable[[str], None] = print,
) -> None:
    """Print user-readable summary output for one cycle."""

    summary = cycle.result.summary
    emit(
        "cycle="
        f"{cycle.cycle_number} run_id={cycle.run_id} status={cycle.result.status.value}"
    )
    emit(
        "summary "
        f"completed={summary.completed_family_count} "
        f"no_available_source_year={summary.no_available_source_year_count} "
        f"failed={summary.failed_family_count} "
        f"parsed_rows={summary.parsed_row_count} "
        f"inserted={summary.inserted_count} "
        f"skipped_duplicates={summary.skipped_duplicate_count}"
    )
    for family in cycle.result.family_results:
        insert_summary = family.insert_summary
        emit(
            "source "
            f"family={family.source_family} "
            f"target_year={family.year_state.target_year} "
            f"latest_year={family.year_state.latest_year} "
            f"status={family.status.value} "
            f"download_status={_download_status_value(family.download_result)} "
            f"parse_status={_parse_status_value(family)} "
            f"parsed_rows={family.parsed_row_count} "
            f"master_inserted={getattr(insert_summary, 'master_inserted', 0)} "
            f"master_skipped={getattr(insert_summary, 'master_skipped', 0)} "
            f"detail_inserted={getattr(insert_summary, 'detail_inserted', 0)} "
            f"detail_skipped={getattr(insert_summary, 'detail_skipped', 0)}"
        )
        for failure in family.failures:
            safe_message = redact_sensitive_text(str(failure.message))
            emit(
                "issue "
                f"family={failure.source_family} stage={failure.stage} "
                f"code={failure.code} message={safe_message}"
            )


def _download_status_value(download_result: object | None) -> str:
    if download_result is None:
        return "not_run"
    return str(getattr(getattr(download_result, "status", None), "value", "unknown"))


def _parse_status_value(family: object) -> str:
    if getattr(family, "parsed_row_count", 0) > 0:
        return "parsed"
    failures = tuple(getattr(family, "failures", ()))
    if any(getattr(failure, "stage", "") == "parser" for failure in failures):
        return "failed"
    download_result = getattr(family, "download_result", None)
    if download_result is None or _download_status_value(download_result) != "downloaded":
        return "not_run"
    return "no_rows"


__all__ = ("emit_configured_cycle_summary",)
