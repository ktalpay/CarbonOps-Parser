namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyRepositoryValidationResult
{
    public IReadOnlyList<SourceFamilyRepositoryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public SourceFamilyRepositoryValidationResult(
        IEnumerable<SourceFamilyRepositoryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
