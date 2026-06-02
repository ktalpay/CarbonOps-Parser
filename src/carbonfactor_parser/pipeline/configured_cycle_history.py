"""Configured ingestion cycle run-history persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionRunHistoryRepository,
    ParserIngestionRunHistoryStatus,
)
from carbonfactor_parser.persistence.ingestion_run_history_mapping import (
    build_ingestion_run_history_command_from_configured_cycle,
)
from carbonfactor_parser.pipeline.configured_cycle_models import ConfiguredCycleResult


def persist_configured_cycle_history(
    cycle: ConfiguredCycleResult,
    *,
    history_repository: ParserIngestionRunHistoryRepository,
    started_at: datetime,
    finished_at: datetime,
    emit: Callable[[str], None] | None,
) -> ConfiguredCycleResult:
    """Persist run-history for a configured cycle without affecting ingestion result."""

    command = build_ingestion_run_history_command_from_configured_cycle(
        cycle,
        started_at=started_at,
        finished_at=finished_at,
    )
    try:
        persist_result = history_repository.persist_ingestion_run_history(command)
    except Exception as exc:  # pragma: no cover - defensive boundary protection
        safe_message = redact_sensitive_text(str(exc))
        if emit is not None:
            emit(
                "history_persistence "
                f"status=failed run_id={cycle.run_id} "
                "issue code=INGESTION_RUN_HISTORY_PERSISTENCE_EXCEPTION "
                f"message={safe_message}"
            )
        return ConfiguredCycleResult(
            cycle_number=cycle.cycle_number,
            run_id=cycle.run_id,
            result=cycle.result,
            history_persistence_status="failed",
            history_persistence_issue_count=1,
        )

    issue_count = len(persist_result.issues)
    if persist_result.status is ParserIngestionRunHistoryStatus.DECLARED:
        if emit is not None:
            emit(f"history_persistence status=declared run_id={cycle.run_id}")
    else:
        if emit is not None:
            for issue in persist_result.issues or ():
                safe_message = redact_sensitive_text(str(issue.message))
                emit(
                    "history_persistence "
                    f"status=failed run_id={cycle.run_id} "
                    f"issue code={issue.code} message={safe_message}"
                )
            if not persist_result.issues:
                emit(
                    "history_persistence "
                    f"status=failed run_id={cycle.run_id} "
                    "issue code=INGESTION_RUN_HISTORY_PERSISTENCE_FAILED "
                    "message=run history persistence failed"
                )
                issue_count = 1
    return ConfiguredCycleResult(
        cycle_number=cycle.cycle_number,
        run_id=cycle.run_id,
        result=cycle.result,
        history_persistence_status=(
            "declared"
            if persist_result.status is ParserIngestionRunHistoryStatus.DECLARED
            else "failed"
        ),
        history_persistence_issue_count=issue_count,
    )


__all__ = ("persist_configured_cycle_history",)
