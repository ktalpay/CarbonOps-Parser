from datetime import date, datetime, timezone

from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapter,
    SourceDocument,
    SourceFamily,
)
from fakes import FakeSourceAdapter, make_adapter_parse_result, make_source_document


def test_source_family_values_exist() -> None:
    assert SourceFamily.GHG_PROTOCOL.value == "ghg_protocol"
    assert SourceFamily.DEFRA_DESNZ.value == "defra_desnz"
    assert SourceFamily.IPCC_EFDB.value == "ipcc_efdb"


def test_source_document_keeps_traceability_fields() -> None:
    retrieved_at = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)

    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA conversion factors",
        source_url="https://example.invalid/defra.xlsx",
        file_reference="data/raw/defra_desnz/example.xlsx",
        source_version="2026",
        publication_date=date(2026, 1, 1),
        retrieved_at=retrieved_at,
        content_hash="abc123",
    )

    assert document.source_family is SourceFamily.DEFRA_DESNZ
    assert document.source_name == "DEFRA conversion factors"
    assert document.source_url == "https://example.invalid/defra.xlsx"
    assert document.file_reference == "data/raw/defra_desnz/example.xlsx"
    assert document.source_version == "2026"
    assert document.publication_date == date(2026, 1, 1)
    assert document.retrieved_at is retrieved_at
    assert document.content_hash == "abc123"


def test_adapter_discovery_result_defaults_are_independent() -> None:
    first = AdapterDiscoveryResult()
    second = AdapterDiscoveryResult()

    first.documents.append(
        SourceDocument(
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="GHG Protocol tool",
        )
    )
    first.warnings.append("unsupported workbook shape")

    assert len(first.documents) == 1
    assert first.warnings == ["unsupported workbook shape"]
    assert second.documents == []
    assert second.warnings == []


def test_adapter_parse_result_represents_handoff_notes() -> None:
    result = AdapterParseResult(
        records=[{"row": 2, "activity": "electricity"}],
        rejected_records=[{"row": 3, "reason": "missing factor value"}],
        warnings=["unknown optional column"],
        normalization_notes=["trimmed whitespace in unit label"],
    )

    assert result.records == [{"row": 2, "activity": "electricity"}]
    assert result.rejected_records == [{"row": 3, "reason": "missing factor value"}]
    assert result.warnings == ["unknown optional column"]
    assert result.normalization_notes == ["trimmed whitespace in unit label"]


def test_in_test_fake_adapter_satisfies_protocol() -> None:
    document = make_source_document(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB export",
        file_reference="data/raw/ipcc_efdb/example.csv",
    )
    adapter = FakeSourceAdapter(
        source_family=SourceFamily.IPCC_EFDB,
        discovery_result=AdapterDiscoveryResult(
            documents=[document],
            warnings=["sample warning"],
        ),
        parse_result=make_adapter_parse_result(
            records=[
                {
                    "source_family": document.source_family.value,
                    "source_name": document.source_name,
                }
            ]
        ),
    )
    discovery = adapter.discover()
    parse_result = adapter.parse(discovery.documents[0])

    assert isinstance(adapter, SourceAdapter)
    assert adapter.source_family is SourceFamily.IPCC_EFDB
    assert discovery.warnings == ["sample warning"]
    assert parse_result.records == [
        {"source_family": "ipcc_efdb", "source_name": "IPCC EFDB export"}
    ]
