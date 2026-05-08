namespace CarbonOps.Parser.Contracts;

public static class ParserSelectionRegistry
{
    public static ParserSelectionBatch CreateDefaultDryRunSelectionBatch() =>
        CreateSelectionBatch(ParserInputRegistry.CreateDefaultDryRunBatch());

    public static ParserSelectionBatch CreateSelectionBatch(ParserInputBatch inputBatch) =>
        new(inputBatch.Documents.Select(CreateSelection));

    public static ParserKey GetParserKey(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => new ParserKey("ghg_protocol_phase1_parser"),
            SourceFamily.DefraDesnz => new ParserKey("defra_desnz_phase1_parser"),
            SourceFamily.IpccEfdb => new ParserKey("ipcc_efdb_phase1_parser"),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static ParserSelection CreateSelection(ParserInputDocument inputDocument) =>
        new(
            inputDocument.SourceFamily,
            GetParserKey(inputDocument.SourceFamily),
            inputDocument);
}
