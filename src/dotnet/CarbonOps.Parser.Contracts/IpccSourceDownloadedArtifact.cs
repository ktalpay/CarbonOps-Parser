namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDownloadedArtifact(
    SourceFamily SourceFamily,
    string SourceKey,
    string CandidateId,
    string ArtifactId,
    string ArtifactKind,
    string SourceReferenceUri,
    string LocalPath,
    string OriginalFilename,
    string ChecksumSha256,
    long SizeBytes,
    DateTimeOffset RetrievedAtUtc,
    string? ContentType = null,
    string? Extension = null,
    string? FinalUri = null,
    int? DocumentYear = null,
    int? ReportingYear = null,
    string? VersionLabel = null);
