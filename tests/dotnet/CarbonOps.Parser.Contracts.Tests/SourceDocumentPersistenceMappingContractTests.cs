using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDocumentPersistenceMappingContractTests
{
    [Fact]
    public void SourceDocumentPersistenceRecordCarriesPersistenceShape()
    {
        var record = new SourceDocumentPersistenceRecord(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);

        Assert.Equal(SourceFamily.DefraDesnz, record.SourceFamily);
        Assert.Equal("defra_desnz_discovery_reference", record.SourceDocumentReference);
        Assert.Equal("dry_run_sha256", record.SourceChecksumAlgorithm);
        Assert.Equal("defra_desnz_dry_run_checksum", record.SourceChecksumValue);
        Assert.True(record.IsDryRunChecksum);
    }

    [Fact]
    public void SourceDocumentPersistenceRecordSupportsImmutableRecordCopy()
    {
        var record = new SourceDocumentPersistenceRecord(
            SourceFamily.GhgProtocol,
            "ghg_protocol_discovery_reference",
            "dry_run_sha256",
            "ghg_protocol_dry_run_checksum",
            IsDryRunChecksum: true);

        var changed = record with { SourceChecksumValue = "ghg_protocol_updated_dry_run_checksum" };

        Assert.Equal("ghg_protocol_dry_run_checksum", record.SourceChecksumValue);
        Assert.Equal("ghg_protocol_updated_dry_run_checksum", changed.SourceChecksumValue);
        Assert.Equal(record.SourceFamily, changed.SourceFamily);
        Assert.Equal(record.SourceDocumentReference, changed.SourceDocumentReference);
    }

    [Fact]
    public void SourceDocumentPersistenceMappingSnapshotsRecords()
    {
        var records = new List<SourceDocumentPersistenceRecord>
        {
            new(
                SourceFamily.IpccEfdb,
                "ipcc_efdb_discovery_reference",
                "dry_run_sha256",
                "ipcc_efdb_dry_run_checksum",
                IsDryRunChecksum: true),
        };

        var mapping = new SourceDocumentPersistenceMapping(records);

        records.Clear();

        Assert.Equal(1, mapping.RecordCount);
        Assert.Single(mapping.Records);
        Assert.Equal(SourceFamily.IpccEfdb, mapping.Records[0].SourceFamily);
    }
}
