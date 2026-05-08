using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserSelectionContractTests
{
    [Fact]
    public void ParserKeyCarriesStableParserIdentifier()
    {
        var parserKey = new ParserKey("defra_desnz_phase1_parser");

        Assert.Equal("defra_desnz_phase1_parser", parserKey.Value);
    }

    [Fact]
    public void ParserSelectionCarriesParserKeyAndInputDocument()
    {
        var inputDocument = new ParserInputDocument(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);
        var parserKey = new ParserKey("defra_desnz_phase1_parser");

        var selection = new ParserSelection(
            SourceFamily.DefraDesnz,
            parserKey,
            inputDocument);

        Assert.Equal(SourceFamily.DefraDesnz, selection.SourceFamily);
        Assert.Equal(parserKey, selection.ParserKey);
        Assert.Equal(inputDocument, selection.InputDocument);
    }

    [Fact]
    public void ParserSelectionBatchSnapshotsSelections()
    {
        var selections = new List<ParserSelection>
        {
            new(
                SourceFamily.IpccEfdb,
                new ParserKey("ipcc_efdb_phase1_parser"),
                new ParserInputDocument(
                    SourceFamily.IpccEfdb,
                    "ipcc_efdb_discovery_reference",
                    ParserSourceFormat.DiscoveryReference,
                    "application/x-carbonops-discovery-reference",
                    "discovery",
                    "dry_run_sha256",
                    "ipcc_efdb_dry_run_checksum",
                    IsDryRunChecksum: true)),
        };

        var batch = new ParserSelectionBatch(selections);

        selections.Clear();

        Assert.Equal(1, batch.SelectionCount);
        Assert.Single(batch.Selections);
        Assert.Equal(SourceFamily.IpccEfdb, batch.Selections[0].SourceFamily);
    }
}
