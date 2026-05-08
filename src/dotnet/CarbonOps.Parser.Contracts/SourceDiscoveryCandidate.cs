namespace CarbonOps.Parser.Contracts;

public sealed record SourceDiscoveryCandidate
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public string CandidateId { get; }

    public string Title { get; }

    public int? ReportingYear { get; }

    public string SourceReference { get; }

    public ParserSourceFormat ExpectedSourceFormat { get; }

    public string ContentType { get; }

    public string? Extension { get; }

    public SourceDocumentChecksum? Checksum { get; }

    public string? VersionLabel { get; }

    public SourceDiscoveryCandidate(
        SourceFamily sourceFamily,
        string sourceKey,
        string candidateId,
        string title,
        int? reportingYear,
        string sourceReference,
        ParserSourceFormat expectedSourceFormat,
        string contentType,
        string? extension = null,
        SourceDocumentChecksum? checksum = null,
        string? versionLabel = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        CandidateId = candidateId;
        Title = title;
        ReportingYear = reportingYear;
        SourceReference = sourceReference;
        ExpectedSourceFormat = expectedSourceFormat;
        ContentType = contentType;
        Extension = extension;
        Checksum = checksum;
        VersionLabel = versionLabel;
    }

    internal static SourceDiscoveryCandidate FromDocumentAndDescriptor(
        SourceDiscoveryDocument document,
        IParserAdapterDescriptor descriptor)
    {
        var sourceFormat = ParserInputRegistry.GetSourceFormat(document.SourceFamily);

        return new SourceDiscoveryCandidate(
            document.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            document.SourceReference,
            document.SourceName,
            document.ReportingYear,
            document.SourceReference,
            sourceFormat,
            ParserInputRegistry.GetContentType(sourceFormat));
    }
}
