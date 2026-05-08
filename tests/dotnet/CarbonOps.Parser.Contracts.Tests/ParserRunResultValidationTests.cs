using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserRunResultValidationTests
{
    [Fact]
    public void ValidParserRunRequestPassesValidation()
    {
        var request = new ParserRunRequest(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);

        var result = request.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ParserRunRequestReportsContractErrors()
    {
        var request = new ParserRunRequest(
            (SourceFamily)999,
            " ",
            "",
            "\t",
            IsDryRunChecksum: true);

        var result = request.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceFamily must be a defined source family.",
                "SourceDocumentReference is required.",
                "SourceChecksumAlgorithm is required.",
                "SourceChecksumValue is required.",
            ],
            result.Errors);
    }

    [Fact]
    public void ParserRunIssueReportsContractErrors()
    {
        var issue = new ParserRunIssue(
            "",
            " ",
            (ParserRunIssueSeverity)999,
            Location: "\t");

        var result = issue.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Code is required.",
                "Message is required.",
                "ParserRunIssueSeverity must be a defined parser run issue severity.",
                "Location must not be whitespace when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void ValidParserRunResultPassesValidation()
    {
        var parserResult = new ParserRunResult(
            new ParserRunRequest(
                SourceFamily.IpccEfdb,
                "ipcc_efdb_discovery_reference",
                "dry_run_sha256",
                "ipcc_efdb_dry_run_checksum",
                IsDryRunChecksum: true),
            ParserRunStatus.Completed,
            totalRows: 4,
            acceptedRows: 3,
            rejectedRows: 1,
            issues:
            [
                new(
                    "PARSER_RUN_WARNING",
                    "Parser run completed with a warning.",
                    ParserRunIssueSeverity.Warning),
            ]);

        var result = parserResult.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ParserRunResultReportsContractErrors()
    {
        var parserResult = new ParserRunResult(
            new ParserRunRequest(
                (SourceFamily)999,
                "",
                "",
                "",
                IsDryRunChecksum: true),
            (ParserRunStatus)999,
            totalRows: -1,
            acceptedRows: -2,
            rejectedRows: -3,
            issues:
            [
                new(
                    "",
                    "",
                    (ParserRunIssueSeverity)999,
                    Location: " "),
            ]);

        var result = parserResult.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Request.SourceFamily must be a defined source family.",
                "Request.SourceDocumentReference is required.",
                "Request.SourceChecksumAlgorithm is required.",
                "Request.SourceChecksumValue is required.",
                "ParserRunStatus must be a defined parser run status.",
                "TotalRows must be non-negative.",
                "AcceptedRows must be non-negative.",
                "RejectedRows must be non-negative.",
                "Issues[0].Code is required.",
                "Issues[0].Message is required.",
                "Issues[0].ParserRunIssueSeverity must be a defined parser run issue severity.",
                "Issues[0].Location must not be whitespace when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void ParserRunResultRejectsCountsAboveTotalRows()
    {
        var parserResult = new ParserRunResult(
            new ParserRunRequest(
                SourceFamily.DefraDesnz,
                "defra_desnz_discovery_reference",
                "dry_run_sha256",
                "defra_desnz_dry_run_checksum",
                IsDryRunChecksum: true),
            ParserRunStatus.Completed,
            totalRows: 2,
            acceptedRows: 2,
            rejectedRows: 1);

        var result = parserResult.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["AcceptedRows plus RejectedRows must not exceed TotalRows."],
            result.Errors);
    }

    [Fact]
    public void DefaultDryRunParserResultSetPassesValidation()
    {
        var resultSet = ParserRunResultRegistry.CreateDefaultDryRunResultSet();

        var result = resultSet.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ParserRunResultSetRejectsDuplicateParserRequests()
    {
        var request = new ParserRunRequest(
            SourceFamily.GhgProtocol,
            "ghg_protocol_discovery_reference",
            "dry_run_sha256",
            "ghg_protocol_dry_run_checksum",
            IsDryRunChecksum: true);
        var resultSet = new ParserRunResultSet(
        [
            new ParserRunResult(
                request,
                ParserRunStatus.Pending,
                totalRows: 0,
                acceptedRows: 0,
                rejectedRows: 0),
            new ParserRunResult(
                request,
                ParserRunStatus.Pending,
                totalRows: 0,
                acceptedRows: 0,
                rejectedRows: 0),
        ]);

        var result = resultSet.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["ParserRunResultSet must not contain duplicate parser run requests."],
            result.Errors);
    }

    [Fact]
    public void ParserRunResultSetPrefixesNestedValidationErrors()
    {
        var resultSet = new ParserRunResultSet(
        [
            new ParserRunResult(
                new ParserRunRequest(
                    SourceFamily.DefraDesnz,
                    " ",
                    "dry_run_sha256",
                    "defra_desnz_dry_run_checksum",
                    IsDryRunChecksum: true),
                (ParserRunStatus)999,
                totalRows: 0,
                acceptedRows: 0,
                rejectedRows: 0),
        ]);

        var result = resultSet.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Results[0].Request.SourceDocumentReference is required.",
                "Results[0].ParserRunStatus must be a defined parser run status.",
            ],
            result.Errors);
    }
}
