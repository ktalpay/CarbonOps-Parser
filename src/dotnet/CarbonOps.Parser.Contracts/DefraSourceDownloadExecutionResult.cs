namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDownloadExecutionResult
{
    public DefraSourceDownloadExecutionStatus Status { get; init; }

    public DefraSourceDownloadExecutionRequest Request { get; init; }

    public DefraSourceDownloadedArtifact? Artifact { get; init; }

    public IReadOnlyList<DefraSourceDownloadExecutionIssue> Issues { get; init; }

    public bool NoParse { get; init; }

    public bool NoDatabaseWrites { get; init; }

    public bool NoSql { get; init; }

    public bool NoScheduler { get; init; }

    public bool Downloaded => Status == DefraSourceDownloadExecutionStatus.Downloaded;

    public DefraSourceDownloadExecutionResult(
        DefraSourceDownloadExecutionStatus status,
        DefraSourceDownloadExecutionRequest request,
        DefraSourceDownloadedArtifact? artifact = null,
        IEnumerable<DefraSourceDownloadExecutionIssue>? issues = null,
        bool noParse = true,
        bool noDatabaseWrites = true,
        bool noSql = true,
        bool noScheduler = true)
    {
        Status = status;
        Request = request;
        Artifact = artifact;
        Issues = (issues ?? Array.Empty<DefraSourceDownloadExecutionIssue>()).ToArray();
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
    }
}
