namespace CarbonOps.Parser.Contracts;

public sealed record ParserInputArtifact
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public ParserSourceFormat SourceFormat { get; }

    public string ArtifactReference { get; }

    public string? DisplayName { get; }

    public string ChecksumAlgorithm { get; }

    public string ChecksumValue { get; }

    public bool IsDryRunChecksum { get; }

    public string ContentType { get; }

    public string? Extension { get; }

    public int? ReportingYear { get; }

    public ParserInputArtifact(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        ParserSourceFormat sourceFormat,
        string artifactReference,
        string? displayName,
        string checksumAlgorithm,
        string checksumValue,
        bool isDryRunChecksum,
        string contentType,
        string? extension,
        int? reportingYear)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        SourceFormat = sourceFormat;
        ArtifactReference = artifactReference;
        DisplayName = displayName;
        ChecksumAlgorithm = checksumAlgorithm;
        ChecksumValue = checksumValue;
        IsDryRunChecksum = isDryRunChecksum;
        ContentType = contentType;
        Extension = extension;
        ReportingYear = reportingYear;
    }

    internal static ParserInputArtifact FromDescriptorAndDocument(
        IParserAdapterDescriptor descriptor,
        ParserInputDocument document) =>
        new(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            document.SourceFormat,
            document.SourceDocumentReference,
            document.SourceDocumentReference,
            document.SourceChecksumAlgorithm,
            document.SourceChecksumValue,
            document.IsDryRunChecksum,
            document.ContentType,
            null,
            null);
}
