namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDiscoveryValidationResult
{
    public IReadOnlyList<IpccSourceDiscoveryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public IpccSourceDiscoveryValidationResult(IEnumerable<IpccSourceDiscoveryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? Array.Empty<IpccSourceDiscoveryIssue>()).ToArray());
    }
}
