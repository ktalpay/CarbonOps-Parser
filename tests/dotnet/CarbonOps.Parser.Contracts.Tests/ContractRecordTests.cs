using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ContractRecordTests
{
    [Fact]
    public void SourceDocumentMetadataCarriesSourceDocumentShape()
    {
        var metadata = new SourceDocumentMetadata(
            SourceFamily.DefraDesnz,
            SourceDocumentStatus.Discovered,
            "DEFRA conversion factors",
            "https://example.test/defra.csv",
            2024,
            "sha256:abc123");

        Assert.Equal(SourceFamily.DefraDesnz, metadata.SourceFamily);
        Assert.Equal(SourceDocumentStatus.Discovered, metadata.SourceDocumentStatus);
        Assert.Equal("DEFRA conversion factors", metadata.SourceName);
        Assert.Equal("https://example.test/defra.csv", metadata.SourceUrl);
        Assert.Equal(2024, metadata.ReportingYear);
        Assert.Equal("sha256:abc123", metadata.Checksum);
    }

    [Fact]
    public void SourceDocumentMetadataSupportsImmutableRecordCopy()
    {
        var discovered = new SourceDocumentMetadata(
            SourceFamily.GhgProtocol,
            SourceDocumentStatus.Discovered,
            "GHG Protocol factors",
            null,
            null,
            null);

        var downloaded = discovered with { SourceDocumentStatus = SourceDocumentStatus.Downloaded };

        Assert.Equal(SourceDocumentStatus.Discovered, discovered.SourceDocumentStatus);
        Assert.Equal(SourceDocumentStatus.Downloaded, downloaded.SourceDocumentStatus);
        Assert.Equal(discovered.SourceFamily, downloaded.SourceFamily);
        Assert.Equal(discovered.SourceName, downloaded.SourceName);
    }

    [Fact]
    public void ParserRunSummaryCarriesParserResultCounts()
    {
        var summary = new ParserRunSummary(
            SourceFamily.IpccEfdb,
            ParserRunStatus.Completed,
            "ipcc-efdb-2024",
            TotalRows: 10,
            AcceptedRows: 8,
            RejectedRows: 2);

        Assert.Equal(SourceFamily.IpccEfdb, summary.SourceFamily);
        Assert.Equal(ParserRunStatus.Completed, summary.ParserRunStatus);
        Assert.Equal("ipcc-efdb-2024", summary.SourceDocumentId);
        Assert.Equal(10, summary.TotalRows);
        Assert.Equal(8, summary.AcceptedRows);
        Assert.Equal(2, summary.RejectedRows);
    }
}
