namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDownloadExecutionResult
{
    public IpccSourceDownloadExecutionStatus Status { get; init; }

    public IpccSourceDownloadExecutionRequest Request { get; init; }

    public IpccSourceDownloadedArtifact? Artifact { get; init; }

    public IReadOnlyList<IpccSourceDownloadExecutionIssue> Issues { get; init; }

    public bool NoParse { get; init; }

    public bool NoDatabaseWrites { get; init; }

    public bool NoSql { get; init; }

    public bool NoScheduler { get; init; }

    public bool Downloaded => Status == IpccSourceDownloadExecutionStatus.Downloaded;

    public bool AlreadyKnown => Status == IpccSourceDownloadExecutionStatus.AlreadyKnown;

    public IpccSourceDownloadExecutionResult(
        IpccSourceDownloadExecutionStatus status,
        IpccSourceDownloadExecutionRequest request,
        IpccSourceDownloadedArtifact? artifact = null,
        IEnumerable<IpccSourceDownloadExecutionIssue>? issues = null,
        bool noParse = true,
        bool noDatabaseWrites = true,
        bool noSql = true,
        bool noScheduler = true)
    {
        Status = status;
        Request = request;
        Artifact = artifact;
        Issues = (issues ?? Array.Empty<IpccSourceDownloadExecutionIssue>()).ToArray();
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
    }
}
