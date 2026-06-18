namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRunRepositoryValidationResult
{
    public IReadOnlyList<SourceAcquisitionRunRepositoryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public SourceAcquisitionRunRepositoryValidationResult(
        IEnumerable<SourceAcquisitionRunRepositoryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
