using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserRunResultRegistryTests
{
    [Fact]
    public void DefaultDryRunParserRequestsContainExactPhaseOneSourceFamilies()
    {
        var requests = ParserRunResultRegistry.CreateDefaultDryRunRequests();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserRequestsUseDeterministicOrder()
    {
        var first = ParserRunResultRegistry.CreateDefaultDryRunRequests();
        var second = ParserRunResultRegistry.CreateDefaultDryRunRequests();

        Assert.Equal(first, second);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Select(request => request.SourceFamily));
    }

    [Fact]
    public void ParserRequestCountMatchesSourceDocumentPersistenceRecords()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var requests = ParserRunResultRegistry.CreateRequests(mapping);

        Assert.Equal(mapping.RecordCount, requests.Count);
        Assert.Equal(
            mapping.Records.Select(record => record.SourceFamily),
            requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserResultSetMatchesSourceDocumentPersistenceRecords()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var resultSet = ParserRunResultRegistry.CreateDryRunResultSet(mapping);

        Assert.Equal(mapping.RecordCount, resultSet.ResultCount);
        Assert.Equal(
            mapping.Records.Select(record => record.SourceFamily),
            resultSet.Results.Select(result => result.Request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserResultsUsePendingStatusAndNonNegativeCounts()
    {
        var resultSet = ParserRunResultRegistry.CreateDefaultDryRunResultSet();

        foreach (var result in resultSet.Results)
        {
            Assert.Equal(ParserRunStatus.Pending, result.Status);
            Assert.True(result.TotalRows >= 0);
            Assert.True(result.AcceptedRows >= 0);
            Assert.True(result.RejectedRows >= 0);
            Assert.Empty(result.Issues);
        }
    }

    [Fact]
    public void DefaultDryRunParserRequestsDoNotContainDuplicates()
    {
        var requests = ParserRunResultRegistry.CreateDefaultDryRunRequests();
        var requestKeys = requests
            .Select(request => $"{request.SourceFamily.ToWireName()}|{request.SourceDocumentReference}|{request.SourceChecksumValue}")
            .ToArray();

        Assert.Equal(requestKeys.Length, requestKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunParserRequestsUseSafeNonNetworkReferences()
    {
        var requests = ParserRunResultRegistry.CreateDefaultDryRunRequests();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            requests.Select(request => request.SourceDocumentReference));

        foreach (var reference in requests.Select(request => request.SourceDocumentReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunParserRequestsDoNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var requests = ParserRunResultRegistry.CreateDefaultDryRunRequests();
        var familyNames = requests
            .SelectMany(request => new[] { request.SourceFamily.ToString(), request.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunParserResultsReturnFreshSnapshots()
    {
        var first = ParserRunResultRegistry.CreateDefaultDryRunResultSet();
        var second = ParserRunResultRegistry.CreateDefaultDryRunResultSet();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Results, second.Results);
        Assert.Equal(first.Results, second.Results);
    }
}
