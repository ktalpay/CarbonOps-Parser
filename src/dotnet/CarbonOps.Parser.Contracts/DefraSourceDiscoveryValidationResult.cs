namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDiscoveryValidationResult
{
    public IReadOnlyList<DefraSourceDiscoveryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public DefraSourceDiscoveryValidationResult(IEnumerable<DefraSourceDiscoveryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? Array.Empty<DefraSourceDiscoveryIssue>()).ToArray());
    }
}
