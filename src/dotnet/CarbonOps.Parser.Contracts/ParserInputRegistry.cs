namespace CarbonOps.Parser.Contracts;

public static class ParserInputRegistry
{
    public static ParserInputBatch CreateDefaultDryRunBatch() =>
        CreateBatch(SourceDocumentPersistenceMapper.MapDefaultDryRunManifest());

    public static ParserInputBatch CreateBatch(SourceDocumentPersistenceMapping mapping) =>
        new(mapping.Records.Select(CreateDocument));

    public static ParserSourceFormat GetSourceFormat(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => ParserSourceFormat.DiscoveryReference,
            SourceFamily.DefraDesnz => ParserSourceFormat.DiscoveryReference,
            SourceFamily.IpccEfdb => ParserSourceFormat.DiscoveryReference,
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    public static string GetContentType(ParserSourceFormat sourceFormat) =>
        sourceFormat switch
        {
            ParserSourceFormat.DiscoveryReference => "application/x-carbonops-discovery-reference",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFormat), sourceFormat, "Unknown parser source format."),
        };

    private static ParserInputDocument CreateDocument(SourceDocumentPersistenceRecord record)
    {
        var sourceFormat = GetSourceFormat(record.SourceFamily);

        return new ParserInputDocument(
            record.SourceFamily,
            record.SourceDocumentReference,
            sourceFormat,
            GetContentType(sourceFormat),
            "discovery",
            record.SourceChecksumAlgorithm,
            record.SourceChecksumValue,
            record.IsDryRunChecksum);
    }
}
