import carbonfactor_parser
from carbonfactor_parser import (
    ArtificialSourceAcquisitionMetadata,
    create_artificial_source_acquisition_metadata,
)
from carbonfactor_parser import source_acquisition


VALID_CHECKSUM = "b" * 64


def test_artificial_metadata_model_imports_from_root_package() -> None:
    assert (
        ArtificialSourceAcquisitionMetadata
        is source_acquisition.ArtificialSourceAcquisitionMetadata
    )
    assert (
        carbonfactor_parser.ArtificialSourceAcquisitionMetadata
        is source_acquisition.ArtificialSourceAcquisitionMetadata
    )


def test_artificial_metadata_factory_imports_from_root_package() -> None:
    assert (
        create_artificial_source_acquisition_metadata
        is source_acquisition.create_artificial_source_acquisition_metadata
    )
    assert (
        carbonfactor_parser.create_artificial_source_acquisition_metadata
        is source_acquisition.create_artificial_source_acquisition_metadata
    )


def test_exported_factory_creates_artificial_metadata_shape() -> None:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="non-authoritative-parser-hint",
        adapter_hint="non-authoritative-adapter-hint",
    )

    assert metadata == ArtificialSourceAcquisitionMetadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="non-authoritative-parser-hint",
        adapter_hint="non-authoritative-adapter-hint",
    )


def test_root_all_lists_source_acquisition_public_symbols_only() -> None:
    assert carbonfactor_parser.__all__ == (
        "ArtificialSourceAcquisitionMetadata",
        "create_artificial_source_acquisition_metadata",
    )
