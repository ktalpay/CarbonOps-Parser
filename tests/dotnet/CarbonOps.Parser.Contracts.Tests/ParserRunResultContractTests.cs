using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserRunResultContractTests
{
    [Fact]
    public void ParserRunRequestCarriesSourceDocumentPersistenceShape()
    {
        var request = new ParserRunRequest(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);

        Assert.Equal(SourceFamily.DefraDesnz, request.SourceFamily);
        Assert.Equal("defra_desnz_discovery_reference", request.SourceDocumentReference);
        Assert.Equal("dry_run_sha256", request.SourceChecksumAlgorithm);
        Assert.Equal("defra_desnz_dry_run_checksum", request.SourceChecksumValue);
        Assert.True(request.IsDryRunChecksum);
    }

    [Fact]
    public void ParserRunIssueCarriesWarningOrErrorShape()
    {
        var issue = new ParserRunIssue(
            "PARSER_RUN_DRY_RUN",
            "Parser run was planned without executing a parser.",
            ParserRunIssueSeverity.Warning,
            Location: "parser_run");

        Assert.Equal("PARSER_RUN_DRY_RUN", issue.Code);
        Assert.Equal("Parser run was planned without executing a parser.", issue.Message);
        Assert.Equal(ParserRunIssueSeverity.Warning, issue.Severity);
        Assert.Equal("parser_run", issue.Location);
    }

    [Fact]
    public void ParserRunResultCarriesRequestStatusCountsAndIssues()
    {
        var request = new ParserRunRequest(
            SourceFamily.IpccEfdb,
            "ipcc_efdb_discovery_reference",
            "dry_run_sha256",
            "ipcc_efdb_dry_run_checksum",
            IsDryRunChecksum: true);
        var issue = new ParserRunIssue(
            "PARSER_RUN_NOT_EXECUTED",
            "Parser run result is a dry-run contract.",
            ParserRunIssueSeverity.Warning);

        var result = new ParserRunResult(
            request,
            ParserRunStatus.Pending,
            totalRows: 0,
            acceptedRows: 0,
            rejectedRows: 0,
            issues: [issue]);

        Assert.Equal(request, result.Request);
        Assert.Equal(ParserRunStatus.Pending, result.Status);
        Assert.Equal(0, result.TotalRows);
        Assert.Equal(0, result.AcceptedRows);
        Assert.Equal(0, result.RejectedRows);
        Assert.Equal([issue], result.Issues);
    }

    [Fact]
    public void ParserRunResultSnapshotsIssues()
    {
        var issues = new List<ParserRunIssue>
        {
            new(
                "PARSER_RUN_DRY_RUN",
                "Parser run was planned without executing a parser.",
                ParserRunIssueSeverity.Warning),
        };
        var result = new ParserRunResult(
            new ParserRunRequest(
                SourceFamily.GhgProtocol,
                "ghg_protocol_discovery_reference",
                "dry_run_sha256",
                "ghg_protocol_dry_run_checksum",
                IsDryRunChecksum: true),
            ParserRunStatus.Pending,
            totalRows: 0,
            acceptedRows: 0,
            rejectedRows: 0,
            issues);

        issues.Clear();

        Assert.Single(result.Issues);
        Assert.Equal("PARSER_RUN_DRY_RUN", result.Issues[0].Code);
    }

    [Fact]
    public void ParserRunResultSetSnapshotsResults()
    {
        var results = new List<ParserRunResult>
        {
            new(
                new ParserRunRequest(
                    SourceFamily.GhgProtocol,
                    "ghg_protocol_discovery_reference",
                    "dry_run_sha256",
                    "ghg_protocol_dry_run_checksum",
                    IsDryRunChecksum: true),
                ParserRunStatus.Pending,
                totalRows: 0,
                acceptedRows: 0,
                rejectedRows: 0),
        };

        var resultSet = new ParserRunResultSet(results);

        results.Clear();

        Assert.Equal(1, resultSet.ResultCount);
        Assert.Single(resultSet.Results);
        Assert.Equal(SourceFamily.GhgProtocol, resultSet.Results[0].Request.SourceFamily);
    }
}
