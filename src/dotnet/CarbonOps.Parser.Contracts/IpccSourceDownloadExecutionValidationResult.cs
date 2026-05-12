namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDownloadExecutionValidationResult
{
    public IReadOnlyList<IpccSourceDownloadExecutionIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public IpccSourceDownloadExecutionValidationResult(
        IEnumerable<IpccSourceDownloadExecutionIssue>? issues = null)
    {
        Issues = (issues ?? Array.Empty<IpccSourceDownloadExecutionIssue>()).ToArray();
    }
}
