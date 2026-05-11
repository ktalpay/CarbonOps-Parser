namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDownloadExecutionValidationResult
{
    public IReadOnlyList<DefraSourceDownloadExecutionIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public DefraSourceDownloadExecutionValidationResult(
        IEnumerable<DefraSourceDownloadExecutionIssue>? issues = null)
    {
        Issues = (issues ?? Array.Empty<DefraSourceDownloadExecutionIssue>()).ToArray();
    }
}
