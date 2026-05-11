namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDiscoveryValidationResult
{
    public IReadOnlyList<GhgSourceDiscoveryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public GhgSourceDiscoveryValidationResult(IEnumerable<GhgSourceDiscoveryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? Array.Empty<GhgSourceDiscoveryIssue>()).ToArray());
    }
}
