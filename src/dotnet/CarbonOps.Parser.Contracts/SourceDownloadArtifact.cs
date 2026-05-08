namespace CarbonOps.Parser.Contracts;

public sealed record SourceDownloadArtifact
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public string CandidateId { get; }

    public string ArtifactId { get; }

    public ParserSourceFormat SourceFormat { get; }

    public string SourceReference { get; }

    public string LocalReference { get; }

    public string? DisplayName { get; }

    public string ContentType { get; }

    public string? Extension { get; }

    public SourceDocumentChecksum? Checksum { get; }

    public long? SizeBytes { get; }

    public int? ReportingYear { get; }

    public string? VersionLabel { get; }

    public SourceDownloadArtifact(
        SourceFamily sourceFamily,
        string sourceKey,
        string candidateId,
        string artifactId,
        ParserSourceFormat sourceFormat,
        string sourceReference,
        string localReference,
        string? displayName,
        string contentType,
        string? extension = null,
        SourceDocumentChecksum? checksum = null,
        long? sizeBytes = null,
        int? reportingYear = null,
        string? versionLabel = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        CandidateId = candidateId;
        ArtifactId = artifactId;
        SourceFormat = sourceFormat;
        SourceReference = sourceReference;
        LocalReference = localReference;
        DisplayName = displayName;
        ContentType = contentType;
        Extension = extension;
        Checksum = checksum;
        SizeBytes = sizeBytes;
        ReportingYear = reportingYear;
        VersionLabel = versionLabel;
    }

    internal static SourceDownloadArtifact FromDiscoveryCandidate(SourceDiscoveryCandidate candidate) =>
        new(
            candidate.SourceFamily,
            candidate.SourceKey,
            candidate.CandidateId,
            $"{candidate.CandidateId}_artifact",
            candidate.ExpectedSourceFormat,
            candidate.SourceReference,
            $"{candidate.CandidateId}_local_artifact",
            candidate.Title,
            candidate.ContentType,
            candidate.Extension,
            candidate.Checksum,
            sizeBytes: null,
            candidate.ReportingYear,
            candidate.VersionLabel);
}
