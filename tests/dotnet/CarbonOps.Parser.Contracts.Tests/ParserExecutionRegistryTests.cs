using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserExecutionRegistryTests
{
    [Fact]
    public void DefaultDryRunParserExecutionRequestsContainExactPhaseOneSourceFamilies()
    {
        var batch = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserExecutionRequestsUseDeterministicOrder()
    {
        var first = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();
        var second = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();

        Assert.Equal(first.Requests, second.Requests);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void ExecutionRequestCountMatchesParserSelectionCount()
    {
        var selectionBatch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var executionBatch = ParserExecutionRegistry.CreateExecutionBatch(selectionBatch);

        Assert.Equal(selectionBatch.SelectionCount, executionBatch.RequestCount);
        Assert.Equal(
            selectionBatch.Selections.Select(selection => selection.SourceFamily),
            executionBatch.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void ParserKeyAndInputMetadataAreCarriedThrough()
    {
        var selectionBatch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var executionBatch = ParserExecutionRegistry.CreateExecutionBatch(selectionBatch);

        Assert.Equal(
            selectionBatch.Selections.Select(selection => selection.ParserKey),
            executionBatch.Requests.Select(request => request.ParserKey));
        Assert.Equal(
            selectionBatch.Selections.Select(selection => selection.InputDocument),
            executionBatch.Requests.Select(request => request.InputDocument));
        Assert.Equal(
            selectionBatch.Selections.Select(selection => selection.ParserKey),
            executionBatch.Requests.Select(request => request.BoundaryDescriptor.ParserKey));
        Assert.Equal(
            selectionBatch.Selections.Select(selection => selection.InputDocument.SourceDocumentReference),
            executionBatch.Requests.Select(request => request.ParserRunRequest.SourceDocumentReference));
    }

    [Fact]
    public void DefaultDryRunExecutionRequestsCreateParserRunRequestsWithoutResults()
    {
        var batch = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();

        foreach (var request in batch.Requests)
        {
            Assert.Equal(request.SourceFamily, request.ParserRunRequest.SourceFamily);
            Assert.Equal(request.InputDocument.SourceDocumentReference, request.ParserRunRequest.SourceDocumentReference);
            Assert.Equal(request.InputDocument.SourceChecksumAlgorithm, request.ParserRunRequest.SourceChecksumAlgorithm);
            Assert.Equal(request.InputDocument.SourceChecksumValue, request.ParserRunRequest.SourceChecksumValue);
            Assert.Equal(request.InputDocument.IsDryRunChecksum, request.ParserRunRequest.IsDryRunChecksum);
        }
    }

    [Fact]
    public void DefaultDryRunExecutionRequestsDoNotContainDuplicates()
    {
        var batch = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();
        var requestKeys = batch.Requests
            .Select(request => $"{request.SourceFamily.ToWireName()}|{request.ParserKey.Value}|{request.InputDocument.SourceDocumentReference}")
            .ToArray();

        Assert.Equal(requestKeys.Length, requestKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunExecutionRequestsUseSafeNonNetworkReferences()
    {
        var batch = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            batch.Requests.Select(request => request.InputDocument.SourceDocumentReference));

        foreach (var reference in batch.Requests.Select(request => request.InputDocument.SourceDocumentReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunExecutionRequestsDoNotIncludePlaceholderParserKeysOrSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var batch = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();
        var names = batch.Requests.SelectMany(request => new[]
        {
            request.SourceFamily.ToString(),
            request.SourceFamily.ToWireName(),
            request.ParserKey.Value,
        });

        foreach (var name in names)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunExecutionBatchesReturnFreshSnapshots()
    {
        var first = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();
        var second = ParserExecutionRegistry.CreateDefaultDryRunExecutionBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Requests, second.Requests);
        Assert.Equal(first.Requests, second.Requests);
    }
}
