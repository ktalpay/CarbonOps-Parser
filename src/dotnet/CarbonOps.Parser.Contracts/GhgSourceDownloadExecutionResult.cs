namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDownloadExecutionResult
{
    public GhgSourceDownloadExecutionStatus Status { get; init; }

    public GhgSourceDownloadExecutionRequest Request { get; init; }

    public GhgSourceDownloadedArtifact? Artifact { get; init; }

    public IReadOnlyList<GhgSourceDownloadExecutionIssue> Issues { get; init; }

    public bool NoParse { get; init; }

    public bool NoDatabaseWrites { get; init; }

    public bool NoSql { get; init; }

    public bool NoScheduler { get; init; }

    public bool Downloaded => Status == GhgSourceDownloadExecutionStatus.Downloaded;

    public GhgSourceDownloadExecutionResult(
        GhgSourceDownloadExecutionStatus status,
        GhgSourceDownloadExecutionRequest request,
        GhgSourceDownloadedArtifact? artifact = null,
        IEnumerable<GhgSourceDownloadExecutionIssue>? issues = null,
        bool noParse = true,
        bool noDatabaseWrites = true,
        bool noSql = true,
        bool noScheduler = true)
    {
        Status = status;
        Request = request;
        Artifact = artifact;
        Issues = (issues ?? Array.Empty<GhgSourceDownloadExecutionIssue>()).ToArray();
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
    }
}
