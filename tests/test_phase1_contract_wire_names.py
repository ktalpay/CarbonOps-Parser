from __future__ import annotations

from carbonfactor_parser.contracts import IngestionStatus, SourceType
from carbonfactor_parser.parsers import ParserExecutionResultStatus
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily as PostgreSQLSourceFamily,
    get_source_family_table_names,
)
from carbonfactor_parser.source_acquisition import (
    ACQUISITION_FAILED_STATUSES,
    ACQUISITION_KNOWN_STATUSES,
    ACQUISITION_SKIPPED_STATUSES,
    ACQUISITION_STATUS_ACQUIRED,
    ACQUISITION_STATUS_FAILED,
    ACQUISITION_STATUS_NOT_IMPLEMENTED,
    ACQUISITION_STATUS_SKIPPED,
    ACQUISITION_SUCCESS_STATUSES,
)
from carbonfactor_parser.source_adapters import (
    IngestionRunStatus,
    SourceFamily as AdapterSourceFamily,
)


def test_phase1_source_family_wire_values_are_stable() -> None:
    expected_external_source_families = (
        ("GHG_PROTOCOL", "ghg_protocol"),
        ("DEFRA_DESNZ", "defra_desnz"),
        ("IPCC_EFDB", "ipcc_efdb"),
    )

    assert tuple((item.name, item.value) for item in SourceType) == (
        expected_external_source_families
    )
    assert tuple((item.name, item.value) for item in AdapterSourceFamily) == (
        expected_external_source_families
    )
    assert tuple(item.value for item in SourceType) == tuple(
        item.value for item in AdapterSourceFamily
    )


def test_phase1_postgresql_source_family_prefixes_are_stable() -> None:
    assert tuple((item.name, item.value) for item in PostgreSQLSourceFamily) == (
        ("GHG", "ghg"),
        ("DEFRA", "defra"),
        ("IPCC", "ipcc"),
    )

    for family in PostgreSQLSourceFamily:
        assert get_source_family_table_names(family) == (
            f"{family.value}_emission_factor_masters",
            f"{family.value}_emission_factor_details",
        )


def test_phase1_ingestion_status_wire_values_are_stable() -> None:
    assert tuple((item.name, item.value) for item in IngestionStatus) == (
        ("PREPARED", "prepared"),
        ("RUNNING", "running"),
        ("SUCCEEDED", "succeeded"),
        ("FAILED", "failed"),
        ("SKIPPED", "skipped"),
    )
    assert tuple((item.name, item.value) for item in IngestionRunStatus) == (
        ("DISCOVERED", "discovered"),
        ("RETRIEVED", "retrieved"),
        ("PARSED", "parsed"),
        ("VALIDATED", "validated"),
        ("COMPLETED", "completed"),
        ("COMPLETED_WITH_WARNINGS", "completed_with_warnings"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
    )


def test_phase1_source_document_status_wire_values_are_stable() -> None:
    assert (
        ACQUISITION_STATUS_ACQUIRED,
        ACQUISITION_STATUS_FAILED,
        ACQUISITION_STATUS_SKIPPED,
        ACQUISITION_STATUS_NOT_IMPLEMENTED,
    ) == (
        "acquired",
        "failed",
        "skipped",
        "not_implemented",
    )
    assert ACQUISITION_SUCCESS_STATUSES == frozenset({"acquired"})
    assert ACQUISITION_FAILED_STATUSES == frozenset({"failed"})
    assert ACQUISITION_SKIPPED_STATUSES == frozenset(
        {"skipped", "not_implemented"}
    )
    assert ACQUISITION_KNOWN_STATUSES == frozenset(
        {"acquired", "failed", "skipped", "not_implemented"}
    )


def test_phase1_parser_run_status_wire_values_are_stable() -> None:
    assert tuple((item.name, item.value) for item in ParserExecutionResultStatus) == (
        ("SUCCESS", "success"),
        ("FAILED", "failed"),
        ("UNSUPPORTED", "unsupported"),
        ("NO_RECORDS", "no_records"),
    )
