"""Tests for parsed emission factor source-family persistence writer."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

from carbonfactor_parser.parsers.file_content_input import ParserFileContentInput
from carbonfactor_parser.parsers.input_artifact_contract import (
    create_phase1_parser_input_artifact,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    create_parser_normalized_output_batch,
    create_parser_normalized_output_row,
)
from carbonfactor_parser.parsers.ghg_protocol_content_parser import (
    parse_ghg_protocol_file_content,
)
from carbonfactor_parser.parsers.defra_desnz_content_parser import (
    parse_defra_desnz_file_content,
)
from carbonfactor_parser.parsers.ipcc_efdb_content_parser import (
    parse_ipcc_efdb_file_content,
)
from carbonfactor_parser.parsers.raw_record import (
    ParsedRawRecord,
    ParsedRawRecordPayload,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
)
from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    ParsedFactorPersistenceStatus,
    build_parsed_factor_persistence_command,
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import SourceFamily
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    create_source_family_repository_persist_result,
)

PARITY_EXPECTATIONS = (
    "tests/fixtures/parity/parsed_factor_persistence_writer_expectations.json"
)


class _FakeSourceFamilyRepository:
    def __init__(self) -> None:
        self.calls: list[
            tuple[
                tuple[SourceFamilyMasterRecord, ...],
                tuple[SourceFamilyDetailRecord, ...],
            ]
        ] = []

    @property
    def provider_name(self) -> str:
        return "fake_source_family"

    def persist_source_family_records(self, master_records, detail_records):
        self.calls.append((tuple(master_records), tuple(detail_records)))
        return create_source_family_repository_persist_result(
            provider_name=self.provider_name,
            master_records=master_records,
            detail_records=detail_records,
        )


def test_writer_maps_defra_payload_into_source_family_records() -> None:
    payload = _defra_payload()

    command = build_parsed_factor_persistence_command(payload)

    assert command.issues == ()
    assert len(command.master_records) == 2
    assert len(command.detail_records) == 2
    master = command.master_records[0]
    detail = command.detail_records[0]
    assert master.source_family is SourceFamily.DEFRA
    assert master.source_document_id.startswith("source_document_")
    assert master.source_family_master_id == (
        "defra_master_2024_conversion-factors-2024_DEFRA-2024-ELEC"
    )
    assert master.master_external_key == "2024:conversion-factors-2024:DEFRA-2024-ELEC"
    assert detail.source_family is SourceFamily.DEFRA
    assert detail.source_family_master_id == master.source_family_master_id
    assert detail.detail_external_key == "DEFRA-2024-ELEC:kWh:CO2e"
    assert detail.factor_value == "0.20705"
    assert detail.factor_unit == "kWh"


def test_writer_maps_normalized_output_batch_with_explicit_source_document() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://ghg/factors.csv",
        reporting_year=2024,
    )
    batch = create_parser_normalized_output_batch(
        (
            create_parser_normalized_output_row(
                artifact=artifact,
                row_id="ghg-row-001",
                source_row_number=2,
                normalized_fields={
                    "source_year": 2024,
                    "source_version": "ghg-2024",
                    "factor_id": "GHG-001",
                    "factor_value": Decimal("1.25"),
                    "factor_unit": "kgco2e",
                },
            ),
        )
    )

    command = build_parsed_factor_persistence_command(
        batch,
        source_document_id="source-document-001",
    )

    assert command.issues == ()
    assert command.master_records[0].source_family is SourceFamily.GHG
    assert command.master_records[0].source_document_id == "source-document-001"
    assert command.detail_records[0].factor_value == "1.25"
    assert command.detail_records[0].factor_unit == "kgco2e"


def test_writer_matches_shared_parity_fixture_for_fallback_persistence_intent() -> None:
    expectations = _parity_expectations()
    row_expectation = expectations["normalized_row"]
    expected_command = expectations["expected_command"]
    artifact = create_phase1_parser_input_artifact(
        source_family=row_expectation["source_family"],
        artifact_reference=row_expectation["artifact_reference"],
        reporting_year=row_expectation["reporting_year"],
    )
    batch = create_parser_normalized_output_batch(
        (
            create_parser_normalized_output_row(
                artifact=artifact,
                row_id=row_expectation["row_id"],
                source_row_number=row_expectation["source_row_number"],
                normalized_fields=dict(row_expectation["fields"]),
            ),
        )
    )

    command = build_parsed_factor_persistence_command(batch)

    assert command.issues == ()
    assert len(command.master_records) == expected_command["master_count"]
    assert len(command.detail_records) == expected_command["detail_count"]
    assert command.skipped_duplicate_count == expected_command["skipped_duplicate_count"]
    master = command.master_records[0]
    detail = command.detail_records[0]
    expected_master = expected_command["master_record"]
    expected_detail = expected_command["detail_record"]
    assert master.source_family.value == expected_master["source_family"]
    assert master.source_family_master_id == expected_master["source_family_master_id"]
    assert master.source_document_id == expected_master["source_document_id"]
    assert master.master_external_key == expected_master["master_external_key"]
    assert master.lifecycle_status == expected_master["lifecycle_status"]
    assert master.record_checksum_sha256 == expected_master["record_checksum_sha256"]
    assert master.created_at == expected_master["created_at"]
    assert master.updated_at == expected_master["updated_at"]
    assert detail.source_family.value == expected_detail["source_family"]
    assert detail.source_family_detail_id == expected_detail["source_family_detail_id"]
    assert detail.source_family_master_id == expected_detail["source_family_master_id"]
    assert detail.detail_external_key == expected_detail["detail_external_key"]
    assert detail.factor_value == expected_detail["factor_value"]
    assert detail.factor_unit == expected_detail["factor_unit"]
    assert detail.lifecycle_status == expected_detail["lifecycle_status"]
    assert detail.record_checksum_sha256 == expected_detail["record_checksum_sha256"]
    assert detail.created_at == expected_detail["created_at"]
    assert detail.updated_at == expected_detail["updated_at"]


def test_writer_persists_ghg_defra_and_ipcc_payloads_with_fake_repository() -> None:
    repository = _FakeSourceFamilyRepository()

    for payload, expected_family in (
        (_ghg_payload(), SourceFamily.GHG),
        (_defra_payload(), SourceFamily.DEFRA),
        (_ipcc_payload(), SourceFamily.IPCC),
    ):
        result = persist_parsed_factor_records(payload, repository)

        assert result.status is ParsedFactorPersistenceStatus.DECLARED
        assert result.persisted_master_count == len(payload.records)
        assert result.persisted_detail_count == len(payload.records)
        assert result.issues == ()
        assert result.command is not None
        assert all(
            record.source_family is expected_family
            for record in result.command.master_records
        )

    assert len(repository.calls) == 3


def test_writer_deduplicates_identical_factor_identity_deterministically() -> None:
    first = _defra_payload().records[0]
    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(first, first),
        source_context={"artifact_reference": "artifact://defra"},
    )

    command = build_parsed_factor_persistence_command(payload)

    assert command.issues == ()
    assert command.skipped_duplicate_count == 2
    assert len(command.master_records) == 1
    assert len(command.detail_records) == 1


def test_writer_rejects_duplicate_factor_identity_with_different_content() -> None:
    first = _defra_payload().records[0]
    conflicting = replace(
        first,
        raw_fields={
            **dict(first.raw_fields),
            "factor_value": Decimal("9.99"),
        },
    )
    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(first, conflicting),
    )

    command = build_parsed_factor_persistence_command(payload)

    assert any(
        issue.code == "PARSED_FACTOR_PERSISTENCE_DUPLICATE_DETAIL_CONFLICT"
        for issue in command.issues
    )


def test_writer_rejects_malformed_input_before_repository_call() -> None:
    repository = _FakeSourceFamilyRepository()
    malformed = ParsedRawRecordPayload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(
            ParsedRawRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=1,
                raw_fields={
                    "factor_id": "DEFRA-001",
                    "factor_value": Decimal("1.2"),
                    "unit": "kgco2e",
                },
            ),
        ),
    )

    result = persist_parsed_factor_records(malformed, repository)

    assert result.status is ParsedFactorPersistenceStatus.FAILED_VALIDATION
    assert repository.calls == []
    assert result.issues[0].code == "PARSED_FACTOR_PERSISTENCE_MISSING_REQUIRED_FIELD"
    assert result.issues[0].field_name == "records[1].source_document_id"


def _ghg_payload():
    result = parse_ghg_protocol_file_content(
        _content_input(
            source_family="ghg_protocol",
            fixture_name="ghg_protocol/ghg_protocol_sample_factors.csv",
        )
    )
    assert result.raw_record_payload is not None
    return result.raw_record_payload


def _defra_payload():
    result = parse_defra_desnz_file_content(
        _content_input(
            source_family="defra_desnz",
            fixture_name="defra_desnz/defra_desnz_normalized_factors.csv",
        )
    )
    assert result.raw_record_payload is not None
    return result.raw_record_payload


def _ipcc_payload():
    result = parse_ipcc_efdb_file_content(
        _content_input(
            source_family="ipcc_efdb",
            fixture_name="ipcc_efdb/ipcc_efdb_sample_factors.csv",
        )
    )
    assert result.raw_record_payload is not None
    return result.raw_record_payload


def _content_input(*, source_family: str, fixture_name: str) -> ParserFileContentInput:
    fixture_path = Path("tests/fixtures/source_documents") / fixture_name
    return ParserFileContentInput(
        source_family=source_family,
        source_id=source_family,
        content=fixture_path.read_text(encoding="utf-8"),
        artifact_reference=str(fixture_path),
        checksum_sha256="c" * 64,
        content_type="text/csv",
        format_hint="csv",
    )


def _parity_expectations() -> dict[str, object]:
    with open(PARITY_EXPECTATIONS, encoding="utf-8") as fixture:
        return json.load(fixture)
