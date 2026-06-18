namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDownloadExecutionValidationResult
{
    public IReadOnlyList<GhgSourceDownloadExecutionIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public GhgSourceDownloadExecutionValidationResult(
        IEnumerable<GhgSourceDownloadExecutionIssue>? issues = null)
    {
        Issues = (issues ?? Array.Empty<GhgSourceDownloadExecutionIssue>()).ToArray();
    }
}
