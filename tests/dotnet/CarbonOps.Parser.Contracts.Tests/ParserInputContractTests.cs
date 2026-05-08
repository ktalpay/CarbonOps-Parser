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
            ParserSourceFormat.Csv,
            "text/csv",
            "csv",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);

        Assert.Equal(SourceFamily.DefraDesnz, document.SourceFamily);
        Assert.Equal("defra_desnz_discovery_reference", document.SourceDocumentReference);
        Assert.Equal(ParserSourceFormat.Csv, document.SourceFormat);
        Assert.Equal("text/csv", document.ContentType);
        Assert.Equal("csv", document.FormatHint);
        Assert.Equal("dry_run_sha256", document.SourceChecksumAlgorithm);
        Assert.Equal("defra_desnz_dry_run_checksum", document.SourceChecksumValue);
        Assert.True(document.IsDryRunChecksum);
    }

    [Fact]
    public void ParserSourceFormatWireNamesAreStable()
    {
        Assert.Equal("csv", ParserSourceFormat.Csv.ToWireName());
        Assert.Equal("xlsx", ParserSourceFormat.Xlsx.ToWireName());
    }

    [Fact]
    public void ParserSourceFormatWireNamesCanBeParsed()
    {
        Assert.True(ContractWireNames.TryParseParserSourceFormatWireName("csv", out var csv));
        Assert.True(ContractWireNames.TryParseParserSourceFormatWireName("xlsx", out var xlsx));
        Assert.False(ContractWireNames.TryParseParserSourceFormatWireName("json", out var invalid));

        Assert.Equal(ParserSourceFormat.Csv, csv);
        Assert.Equal(ParserSourceFormat.Xlsx, xlsx);
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
                ParserSourceFormat.Csv,
                "text/csv",
                "csv",
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
