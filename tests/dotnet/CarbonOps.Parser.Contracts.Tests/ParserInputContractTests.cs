using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserInputContractTests
{
    [Fact]
    public void ParserInputDocumentCarriesParserInputShape()
    {
        var document = new ParserInputDocument(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);

        Assert.Equal(SourceFamily.DefraDesnz, document.SourceFamily);
        Assert.Equal("defra_desnz_discovery_reference", document.SourceDocumentReference);
        Assert.Equal(ParserSourceFormat.DiscoveryReference, document.SourceFormat);
        Assert.Equal("application/x-carbonops-discovery-reference", document.ContentType);
        Assert.Equal("discovery", document.FormatHint);
        Assert.Equal("dry_run_sha256", document.SourceChecksumAlgorithm);
        Assert.Equal("defra_desnz_dry_run_checksum", document.SourceChecksumValue);
        Assert.True(document.IsDryRunChecksum);
    }

    [Fact]
    public void ParserSourceFormatWireNamesAreStable()
    {
        Assert.Equal("discovery_reference", ParserSourceFormat.DiscoveryReference.ToWireName());
    }

    [Fact]
    public void ParserSourceFormatWireNamesCanBeParsed()
    {
        Assert.True(ContractWireNames.TryParseParserSourceFormatWireName("discovery_reference", out var format));
        Assert.False(ContractWireNames.TryParseParserSourceFormatWireName("csv", out var invalid));

        Assert.Equal(ParserSourceFormat.DiscoveryReference, format);
        Assert.Equal(default, invalid);
    }

    [Fact]
    public void ParserInputBatchSnapshotsDocuments()
    {
        var documents = new List<ParserInputDocument>
        {
            new(
                SourceFamily.IpccEfdb,
                "ipcc_efdb_discovery_reference",
                ParserSourceFormat.DiscoveryReference,
                "application/x-carbonops-discovery-reference",
                "discovery",
                "dry_run_sha256",
                "ipcc_efdb_dry_run_checksum",
                IsDryRunChecksum: true),
        };

        var batch = new ParserInputBatch(documents);

        documents.Clear();

        Assert.Equal(1, batch.DocumentCount);
        Assert.Single(batch.Documents);
        Assert.Equal(SourceFamily.IpccEfdb, batch.Documents[0].SourceFamily);
    }
}
