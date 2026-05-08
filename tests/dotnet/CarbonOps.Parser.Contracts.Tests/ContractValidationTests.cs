using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ContractValidationTests
{
    [Fact]
    public void ValidSourceDocumentMetadataPassesValidation()
    {
        var metadata = new SourceDocumentMetadata(
            SourceFamily.DefraDesnz,
            SourceDocumentStatus.Downloaded,
            "DEFRA conversion factors",
            "defra-source-placeholder.csv",
            2024,
            "sha256:abc123");

        var result = metadata.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void SourceDocumentMetadataReportsContractErrors()
    {
        var metadata = new SourceDocumentMetadata(
            (SourceFamily)999,
            (SourceDocumentStatus)999,
            " ",
            " ",
            1800,
            " ");

        var result = metadata.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceFamily must be a defined source family.",
                "SourceDocumentStatus must be a defined source document status.",
                "SourceName is required.",
                "SourceUrl must not be whitespace when provided.",
                "Checksum must not be whitespace when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void SourceDocumentMetadataAllowsMissingOptionalFields()
    {
        var metadata = new SourceDocumentMetadata(
            SourceFamily.GhgProtocol,
            SourceDocumentStatus.Discovered,
            "GHG Protocol factors",
            null,
            null,
            null);

        Assert.True(metadata.Validate().IsValid);
    }

    [Fact]
    public void ValidParserRunSummaryPassesValidation()
    {
        var summary = new ParserRunSummary(
            SourceFamily.IpccEfdb,
            ParserRunStatus.Completed,
            "ipcc-efdb-2024",
            TotalRows: 10,
            AcceptedRows: 8,
            RejectedRows: 2);

        var result = summary.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ParserRunSummaryReportsContractErrors()
    {
        var summary = new ParserRunSummary(
            (SourceFamily)999,
            (ParserRunStatus)999,
            "",
            TotalRows: -1,
            AcceptedRows: -2,
            RejectedRows: -3);

        var result = summary.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceFamily must be a defined source family.",
                "ParserRunStatus must be a defined parser run status.",
                "SourceDocumentId is required.",
                "TotalRows must be non-negative.",
                "AcceptedRows must be non-negative.",
                "RejectedRows must be non-negative.",
            ],
            result.Errors);
    }

    [Fact]
    public void ParserRunSummaryRejectsCountsAboveTotalRows()
    {
        var summary = new ParserRunSummary(
            SourceFamily.DefraDesnz,
            ParserRunStatus.Completed,
            "defra-2024",
            TotalRows: 2,
            AcceptedRows: 2,
            RejectedRows: 1);

        var result = summary.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["AcceptedRows plus RejectedRows must not exceed TotalRows."],
            result.Errors);
    }
}
