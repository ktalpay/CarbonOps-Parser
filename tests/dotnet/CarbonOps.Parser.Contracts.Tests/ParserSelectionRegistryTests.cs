using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserSelectionRegistryTests
{
    [Fact]
    public void DefaultDryRunParserSelectionsContainExactPhaseOneSourceFamilies()
    {
        var batch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Selections.Select(selection => selection.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserSelectionsUseDeterministicOrder()
    {
        var first = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var second = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();

        Assert.Equal(first.Selections, second.Selections);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Selections.Select(selection => selection.SourceFamily));
    }

    [Fact]
    public void ParserSelectionCountMatchesParserInputCount()
    {
        var inputBatch = ParserInputRegistry.CreateDefaultDryRunBatch();
        var selectionBatch = ParserSelectionRegistry.CreateSelectionBatch(inputBatch);

        Assert.Equal(inputBatch.DocumentCount, selectionBatch.SelectionCount);
        Assert.Equal(
            inputBatch.Documents.Select(document => document.SourceFamily),
            selectionBatch.Selections.Select(selection => selection.SourceFamily));
    }

    [Fact]
    public void ParserKeyMappingIsExplicitAndStable()
    {
        var batch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();

        Assert.Equal(
            [
                "ghg_protocol_phase1_parser",
                "defra_desnz_phase1_parser",
                "ipcc_efdb_phase1_parser",
            ],
            batch.Selections.Select(selection => selection.ParserKey.Value));
        Assert.Equal("ghg_protocol_phase1_parser", ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol).Value);
        Assert.Equal("defra_desnz_phase1_parser", ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz).Value);
        Assert.Equal("ipcc_efdb_phase1_parser", ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb).Value);
    }

    [Fact]
    public void ParserSelectionsCarryParserInputsThrough()
    {
        var inputBatch = ParserInputRegistry.CreateDefaultDryRunBatch();
        var selectionBatch = ParserSelectionRegistry.CreateSelectionBatch(inputBatch);

        Assert.Equal(
            inputBatch.Documents,
            selectionBatch.Selections.Select(selection => selection.InputDocument));
    }

    [Fact]
    public void DefaultDryRunParserSelectionsDoNotContainDuplicateParserKeys()
    {
        var batch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var parserKeys = batch.Selections
            .Select(selection => selection.ParserKey.Value)
            .ToArray();

        Assert.Equal(parserKeys.Length, parserKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunParserSelectionsUseSafeNonNetworkReferences()
    {
        var batch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            batch.Selections.Select(selection => selection.InputDocument.SourceDocumentReference));

        foreach (var reference in batch.Selections.Select(selection => selection.InputDocument.SourceDocumentReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunParserSelectionsDoNotIncludePlaceholderParserKeysOrSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var batch = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var names = batch.Selections.SelectMany(selection => new[]
        {
            selection.SourceFamily.ToString(),
            selection.SourceFamily.ToWireName(),
            selection.ParserKey.Value,
        });

        foreach (var name in names)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunParserSelectionBatchesReturnFreshSnapshots()
    {
        var first = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();
        var second = ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Selections, second.Selections);
        Assert.Equal(first.Selections, second.Selections);
    }
}
