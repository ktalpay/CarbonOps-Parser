"""Mapping from configured ingestion cycles to run-history commands."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Mapping

from carbonfactor_parser.diagnostics.ingestion_runtime_events import (
    configured_download_status_value,
    configured_parse_status_value,
    iter_deduplicated_ingestion_issues,
)
from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionIssueRecord,
    ParserIngestionRunHistoryCommand,
    ParserIngestionRunRecord,
    ParserIngestionSourceResultRecord,
)
if TYPE_CHECKING:
    from carbonfactor_parser.pipeline.configured_cycle_runner import ConfiguredCycleResult


def build_ingestion_run_history_command_from_configured_cycle(
    cycle: "ConfiguredCycleResult",
    *,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    trigger_type: str = "operator",
    metadata: Mapping[str, object] | None = None,
) -> ParserIngestionRunHistoryCommand:
    """Build a parser run-history persistence command for a configured cycle."""

    safe_started_at = started_at or datetime.now(timezone.utc)
    safe_finished_at = finished_at or datetime.now(timezone.utc)
    result = cycle.result
    summary = result.summary
    run_metadata: dict[str, object] = {
        "requested_family_count": summary.requested_family_count,
        "completed_family_count": summary.completed_family_count,
        "failed_family_count": summary.failed_family_count,
        "no_available_source_year_count": summary.no_available_source_year_count,
    }
    if metadata:
        run_metadata.update(dict(metadata))

    source_results = tuple(
        _source_result_record(cycle.run_id, family)
        for family in result.family_results
    )
    issues = tuple(
        _issue_record(
            cycle.run_id,
            issue,
            target_year_by_source_family=_target_year_by_source_family(result.family_results),
        )
        for issue in iter_deduplicated_ingestion_issues(result)
    )

    return ParserIngestionRunHistoryCommand(
        run=ParserIngestionRunRecord(
            run_id=cycle.run_id,
            started_at=safe_started_at,
            finished_at=safe_finished_at,
            status=result.status.value,
            trigger_type=trigger_type,
            enabled_source_families=tuple(result.selected_source_families),
            initial_year=result.request.initial_year,
            cycle_count=cycle.cycle_number,
            total_parsed_rows=summary.parsed_row_count,
            total_inserted_count=summary.inserted_count,
            total_skipped_duplicate_count=summary.skipped_duplicate_count,
            failure_count=summary.failure_count,
            metadata=run_metadata,
        ),
        source_results=source_results,
        issues=issues,
    )


def _source_result_record(
    run_id: str,
    family: object,
) -> ParserIngestionSourceResultRecord:
    year_state = getattr(family, "year_state")
    validation_result = getattr(family, "validation_result", None)
    insert_summary = getattr(family, "insert_summary", None)
    metadata = {
        "selection_status": getattr(
            getattr(year_state, "selection_status", None),
            "value",
            getattr(year_state, "selection_status", None),
        ),
        "recorded_ingested_year": getattr(family, "recorded_ingested_year", None),
    }
    return ParserIngestionSourceResultRecord(
        run_id=run_id,
        source_family=getattr(family, "source_family"),
        target_year=getattr(year_state, "target_year"),
        latest_year=getattr(year_state, "latest_year"),
        status=_status_value(getattr(family, "status", None)),
        download_status=configured_download_status_value(
            getattr(family, "download_result", None),
        ),
        parse_status=configured_parse_status_value(family),
        validation_status=(
            _status_value(getattr(validation_result, "status", None))
            if validation_result is not None
            else None
        ),
        insert_status=(
            _status_value(getattr(insert_summary, "status", None))
            if insert_summary is not None
            else None
        ),
        parsed_rows=getattr(family, "parsed_row_count", 0),
        master_inserted=getattr(insert_summary, "master_inserted", 0),
        master_skipped=getattr(insert_summary, "master_skipped", 0),
        detail_inserted=getattr(insert_summary, "detail_inserted", 0),
        detail_skipped=getattr(insert_summary, "detail_skipped", 0),
        issue_count=len(tuple(getattr(family, "failures", ()))),
        metadata={key: value for key, value in metadata.items() if value is not None},
    )


def _status_value(status: object | None) -> str | None:
    if status is None:
        return None
    return str(getattr(status, "value", status))


def _issue_record(
    run_id: str,
    issue: object,
    *,
    target_year_by_source_family: Mapping[str, int],
) -> ParserIngestionIssueRecord:
    source_family = getattr(issue, "source_family", None)
    return ParserIngestionIssueRecord(
        run_id=run_id,
        source_family=source_family,
        target_year=(
            target_year_by_source_family.get(source_family)
            if source_family is not None
            else None
        ),
        stage=str(getattr(issue, "stage")),
        code=str(getattr(issue, "code")),
        severity=str(getattr(issue, "severity", "error")),
        field_name=getattr(issue, "field_name", None),
        message=redact_sensitive_text(str(getattr(issue, "message"))),
    )


def _target_year_by_source_family(family_results: object) -> dict[str, int]:
    target_years: dict[str, int] = {}
    for family in family_results:
        year_state = getattr(family, "year_state")
        target_years[getattr(family, "source_family")] = getattr(
            year_state,
            "target_year",
        )
    return target_years


__all__ = ("build_ingestion_run_history_command_from_configured_cycle",)
