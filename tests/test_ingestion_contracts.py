"""Tests for shared ingestion contract boundaries."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from carbonfactor_parser.contracts import (
    IngestionRun,
    IngestionStatus,
    ParsedFactorRecord,
    PersistenceBootstrapResult,
    SourceAcquisitionResult,
    SourceDocument,
    SourceType,
)


def test_contracts_public_imports() -> None:
    assert SourceType.GHG_PROTOCOL.value == "ghg_protocol"
    assert SourceDocument.__name__ == "SourceDocument"
    assert SourceAcquisitionResult.__name__ == "SourceAcquisitionResult"
    assert ParsedFactorRecord.__name__ == "ParsedFactorRecord"
    assert IngestionRun.__name__ == "IngestionRun"
    assert IngestionStatus.SUCCEEDED.value == "succeeded"
    assert PersistenceBootstrapResult.__name__ == "PersistenceBootstrapResult"


def test_source_type_values_are_stable() -> None:
    assert tuple(item.value for item in SourceType) == (
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    )


def test_ingestion_status_values_are_stable() -> None:
    assert tuple(item.value for item in IngestionStatus) == (
        "prepared",
        "running",
        "succeeded",
        "failed",
        "skipped",
    )


def test_contract_construction() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    source_document = SourceDocument(
        source_type=SourceType.DEFRA_DESNZ,
        source_name="DEFRA/DESNZ",
        document_id="doc-001",
        source_uri="https://example.invalid/defra.csv",
        local_path="fixtures/defra.csv",
        source_version="2026.1",
        acquired_at=now,
        content_hash="abc123",
    )
    acquisition_result = SourceAcquisitionResult(
        status=IngestionStatus.SUCCEEDED,
        source_type=SourceType.DEFRA_DESNZ,
        run_id="run-001",
        started_at=now,
        completed_at=now,
        documents=(source_document,),
        warnings=("none",),
    )
    record = ParsedFactorRecord(
        record_id="rec-001",
        source_type=SourceType.DEFRA_DESNZ,
        factor_value=1.23,
        factor_unit="kg_co2e",
        activity_unit="kwh",
        gas="co2",
    )
    run = IngestionRun(
        run_id="run-001",
        source_type=SourceType.DEFRA_DESNZ,
        status=IngestionStatus.SUCCEEDED,
        started_at=now,
        completed_at=now,
        acquired_document_count=1,
        parsed_record_count=1,
    )
    bootstrap = PersistenceBootstrapResult(
        status=IngestionStatus.PREPARED,
        backend_name="postgresql",
        ready=False,
        schema_version="phase1",
        details={"reason": "not connected"},
    )

    assert acquisition_result.documents[0] == source_document
    assert record.factor_unit == "kg_co2e"
    assert run.parsed_record_count == 1
    assert bootstrap.ready is False


def test_frozen_contract_instances_are_immutable() -> None:
    document = SourceDocument(
        source_type=SourceType.GHG_PROTOCOL,
        source_name="GHG Protocol",
        document_id="ghg-1",
    )

    with pytest.raises(FrozenInstanceError):
        document.document_id = "updated"  # type: ignore[misc]


def test_contract_package_import_has_no_runtime_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import importlib
    import sys

    removed_modules = [
        module_name
        for module_name in list(sys.modules)
        if module_name == "carbonfactor_parser.contracts"
        or module_name.startswith("carbonfactor_parser.contracts.")
    ]
    for module_name in removed_modules:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    open_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError(
            "carbonfactor_parser.contracts import attempted file open side effects"
        )

    monkeypatch.setattr(builtins, "open", guard_open)

    imported_modules_before = set(sys.modules)
    module = importlib.import_module("carbonfactor_parser.contracts")
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "SourceType")
    assert hasattr(module, "IngestionRun")
    assert open_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    banned_prefixes = ("requests", "psycopg", "sqlalchemy", "dotenv")
    assert not any(name.startswith(banned_prefixes) for name in newly_imported)
