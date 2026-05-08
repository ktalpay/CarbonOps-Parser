namespace CarbonOps.Parser.Contracts;

public sealed record SourceArtifactParserInputBridge
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public string SourceArtifactId { get; }

    public string ParserInputArtifactId { get; }

    public SourceDownloadArtifact SourceArtifact { get; }

    public ParserInputArtifact ParserInputArtifact { get; }

    public SourceArtifactParserInputBridge(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        string sourceArtifactId,
        string parserInputArtifactId,
        SourceDownloadArtifact sourceArtifact,
        ParserInputArtifact parserInputArtifact)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        SourceArtifactId = sourceArtifactId;
        ParserInputArtifactId = parserInputArtifactId;
        SourceArtifact = sourceArtifact;
        ParserInputArtifact = parserInputArtifact;
    }

    internal static SourceArtifactParserInputBridge FromSourceArtifact(
        SourceDownloadArtifact sourceArtifact,
        IParserAdapterDescriptor descriptor)
    {
        var checksum = sourceArtifact.Checksum ?? new SourceDocumentChecksum(
            "not_supplied",
            $"{sourceArtifact.ArtifactId}_checksum_not_supplied",
            IsDryRunPlaceholder: true);
        var parserInputArtifact = new ParserInputArtifact(
            sourceArtifact.SourceFamily,
            sourceArtifact.SourceKey,
            descriptor.ParserKey,
            sourceArtifact.SourceFormat,
            sourceArtifact.LocalReference,
            sourceArtifact.DisplayName,
            checksum.Algorithm,
            checksum.Value,
            checksum.IsDryRunPlaceholder,
            sourceArtifact.ContentType,
            sourceArtifact.Extension,
            sourceArtifact.ReportingYear);

        return new SourceArtifactParserInputBridge(
            sourceArtifact.SourceFamily,
            sourceArtifact.SourceKey,
            descriptor.ParserKey,
            sourceArtifact.ArtifactId,
            $"{sourceArtifact.ArtifactId}_parser_input",
            sourceArtifact,
            parserInputArtifact);
    }
}
