namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDocumentCandidate
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public string CandidateId { get; }

    public string Title { get; }

    public string ReferenceUri { get; }

    public string ArtifactKind { get; }

    public DefraSourceDiscoveryStatus Status { get; }

    public int? DocumentYear { get; }

    public int? ReportingYear { get; }

    public string? ContentType { get; }

    public string? Extension { get; }

    public string? ChecksumSha256 { get; }

    public string? VersionLabel { get; }

    public string? DiscoveredAtLabel { get; }

    public bool DownloadAllowed { get; }

    public DefraSourceDocumentCandidate(
        SourceFamily sourceFamily,
        string sourceKey,
        string candidateId,
        string title,
        string referenceUri,
        string artifactKind,
        DefraSourceDiscoveryStatus status = DefraSourceDiscoveryStatus.Declared,
        int? documentYear = null,
        int? reportingYear = null,
        string? contentType = null,
        string? extension = null,
        string? checksumSha256 = null,
        string? versionLabel = null,
        string? discoveredAtLabel = null,
        bool downloadAllowed = false)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        CandidateId = candidateId;
        Title = title;
        ReferenceUri = referenceUri;
        ArtifactKind = artifactKind;
        Status = status;
        DocumentYear = documentYear;
        ReportingYear = reportingYear;
        ContentType = contentType;
        Extension = extension;
        ChecksumSha256 = checksumSha256;
        VersionLabel = versionLabel;
        DiscoveredAtLabel = discoveredAtLabel;
        DownloadAllowed = downloadAllowed;
    }
}
