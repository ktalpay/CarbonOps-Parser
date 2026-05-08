using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDocumentManifestContractTests
{
    [Fact]
    public void SourceDocumentChecksumCarriesDeterministicPlaceholderShape()
    {
        var checksum = new SourceDocumentChecksum(
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunPlaceholder: true);

        Assert.Equal("dry_run_sha256", checksum.Algorithm);
        Assert.Equal("defra_desnz_dry_run_checksum", checksum.Value);
        Assert.True(checksum.IsDryRunPlaceholder);
    }

    [Fact]
    public void SourceDocumentManifestEntryCarriesManifestMetadata()
    {
        var checksum = new SourceDocumentChecksum(
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunPlaceholder: true);
        var entry = new SourceDocumentManifestEntry(
            SourceFamily.DefraDesnz,
            "DEFRA/DESNZ",
            "defra_desnz_discovery_reference",
            checksum);

        Assert.Equal(SourceFamily.DefraDesnz, entry.SourceFamily);
        Assert.Equal("DEFRA/DESNZ", entry.SourceName);
        Assert.Equal("defra_desnz_discovery_reference", entry.SourceReference);
        Assert.Equal(checksum, entry.Checksum);
    }

    [Fact]
    public void SourceDocumentManifestEntrySupportsImmutableRecordCopy()
    {
        var entry = new SourceDocumentManifestEntry(
            SourceFamily.GhgProtocol,
            "GHG Protocol",
            "ghg_protocol_discovery_reference",
            new SourceDocumentChecksum(
                "dry_run_sha256",
                "ghg_protocol_dry_run_checksum",
                IsDryRunPlaceholder: true));

        var renamed = entry with { SourceName = "GHG Protocol factors" };

        Assert.Equal("GHG Protocol", entry.SourceName);
        Assert.Equal("GHG Protocol factors", renamed.SourceName);
        Assert.Equal(entry.SourceFamily, renamed.SourceFamily);
        Assert.Equal(entry.Checksum, renamed.Checksum);
    }

    [Fact]
    public void SourceDocumentManifestSnapshotsEntries()
    {
        var entries = new List<SourceDocumentManifestEntry>
        {
            new(
                SourceFamily.IpccEfdb,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference",
                new SourceDocumentChecksum(
                    "dry_run_sha256",
                    "ipcc_efdb_dry_run_checksum",
                    IsDryRunPlaceholder: true)),
        };

        var manifest = new SourceDocumentManifest(entries);

        entries.Clear();

        Assert.Equal(1, manifest.EntryCount);
        Assert.Single(manifest.Entries);
        Assert.Equal(SourceFamily.IpccEfdb, manifest.Entries[0].SourceFamily);
    }
}
