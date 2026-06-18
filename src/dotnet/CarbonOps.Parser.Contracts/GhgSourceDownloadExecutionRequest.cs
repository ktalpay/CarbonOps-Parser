namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDownloadExecutionRequest
{
    public SourceFamily SourceFamily { get; init; }

    public string SourceKey { get; init; }

    public string CandidateId { get; init; }

    public string CandidateTitle { get; init; }

    public string SourceReferenceUri { get; init; }

    public string ArtifactKind { get; init; }

    public string TargetRoot { get; init; }

    public string TargetRelativePath { get; init; }

    public bool CandidateDownloadAllowed { get; init; }

    public bool AllowDownloadExecution { get; init; }

    public bool AllowFileWrite { get; init; }

    public bool AllowNetwork { get; init; }

    public bool AllowOverwrite { get; init; }

    public bool AllowParse { get; init; }

    public bool AllowDatabaseWrites { get; init; }

    public bool AllowScheduler { get; init; }

    public string? ContentType { get; init; }

    public string? Extension { get; init; }

    public string? ExpectedChecksumSha256 { get; init; }

    public int? DocumentYear { get; init; }

    public int? ReportingYear { get; init; }

    public string? VersionLabel { get; init; }

    public GhgSourceDownloadExecutionRequest(
        SourceFamily sourceFamily,
        string sourceKey,
        string candidateId,
        string candidateTitle,
        string sourceReferenceUri,
        string artifactKind,
        string targetRoot,
        string targetRelativePath,
        bool candidateDownloadAllowed = false,
        bool allowDownloadExecution = false,
        bool allowFileWrite = false,
        bool allowNetwork = false,
        bool allowOverwrite = false,
        bool allowParse = false,
        bool allowDatabaseWrites = false,
        bool allowScheduler = false,
        string? contentType = null,
        string? extension = null,
        string? expectedChecksumSha256 = null,
        int? documentYear = null,
        int? reportingYear = null,
        string? versionLabel = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        CandidateId = candidateId;
        CandidateTitle = candidateTitle;
        SourceReferenceUri = sourceReferenceUri;
        ArtifactKind = artifactKind;
        TargetRoot = targetRoot;
        TargetRelativePath = targetRelativePath;
        CandidateDownloadAllowed = candidateDownloadAllowed;
        AllowDownloadExecution = allowDownloadExecution;
        AllowFileWrite = allowFileWrite;
        AllowNetwork = allowNetwork;
        AllowOverwrite = allowOverwrite;
        AllowParse = allowParse;
        AllowDatabaseWrites = allowDatabaseWrites;
        AllowScheduler = allowScheduler;
        ContentType = contentType;
        Extension = extension;
        ExpectedChecksumSha256 = expectedChecksumSha256;
        DocumentYear = documentYear;
        ReportingYear = reportingYear;
        VersionLabel = versionLabel;
    }
}
