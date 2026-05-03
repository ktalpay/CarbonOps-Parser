from pathlib import Path

from carbonfactor_parser.source_adapters import (
    DefraDesnzFixtureManifest,
    DefraDesnzFixtureManifestEntry,
    DefraDesnzSourceAdapter,
    SourceDocument,
    SourceFamily,
    build_defra_desnz_fixture_manifest,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[0] / "fixtures" / "source_documents" / "defra_desnz"
)


def test_manifest_can_be_created_from_no_documents() -> None:
    manifest = build_defra_desnz_fixture_manifest(())

    assert isinstance(manifest, DefraDesnzFixtureManifest)
    assert manifest.source_family == SourceFamily.DEFRA_DESNZ
    assert manifest.source_name == "defra_desnz"
    assert manifest.document_count == 0
    assert manifest.entries == ()
    assert manifest.is_artificial_fixture is True


def test_manifest_can_be_created_from_defra_desnz_fixture_documents() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents

    manifest = build_defra_desnz_fixture_manifest(documents)

    assert manifest.document_count == 2
    assert [entry.file_name for entry in manifest.entries] == [
        "defra_desnz_metadata.json",
        "defra_desnz_sample_factors.csv",
    ]


def test_manifest_entry_ordering_is_deterministic() -> None:
    documents = (
        SourceDocument(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="defra_desnz:z.csv",
            file_reference=str(FIXTURE_DIRECTORY / "z.csv"),
        ),
        SourceDocument(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="defra_desnz:a.json",
            file_reference=str(FIXTURE_DIRECTORY / "a.json"),
        ),
    )

    manifest = build_defra_desnz_fixture_manifest(documents)

    assert [entry.file_name for entry in manifest.entries] == [
        "a.json",
        "z.csv",
    ]


def test_manifest_derives_file_names_and_extensions() -> None:
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="defra_desnz:source.CSV",
        file_reference=str(FIXTURE_DIRECTORY / "source.CSV"),
    )

    manifest = build_defra_desnz_fixture_manifest((document,))
    entry = manifest.entries[0]

    assert isinstance(entry, DefraDesnzFixtureManifestEntry)
    assert entry.file_name == "source.CSV"
    assert entry.file_extension == ".csv"
    assert entry.path_reference == str(FIXTURE_DIRECTORY / "source.CSV")


def test_manifest_marks_entries_as_artificial_fixtures() -> None:
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="defra_desnz:source.csv",
        file_reference=str(FIXTURE_DIRECTORY / "source.csv"),
    )

    manifest = build_defra_desnz_fixture_manifest((document,))

    assert manifest.is_artificial_fixture is True
    assert manifest.entries[0].is_artificial_fixture is True


def test_manifest_does_not_parse_fixture_contents() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents

    manifest = build_defra_desnz_fixture_manifest(documents)

    assert "Artificial local fixture" not in str(manifest)
    assert "adapter skeleton discovery" not in str(manifest)


def test_manifest_uses_discovered_document_metadata() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents

    manifest = build_defra_desnz_fixture_manifest(documents)

    assert [entry.source_family for entry in manifest.entries] == [
        SourceFamily.DEFRA_DESNZ,
        SourceFamily.DEFRA_DESNZ,
    ]
    assert [entry.source_name for entry in manifest.entries] == [
        "defra_desnz:defra_desnz_metadata.json",
        "defra_desnz:defra_desnz_sample_factors.csv",
    ]
