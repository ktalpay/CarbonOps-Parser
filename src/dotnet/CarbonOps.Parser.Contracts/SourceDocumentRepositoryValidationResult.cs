namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentRepositoryValidationResult
{
    public IReadOnlyList<SourceDocumentRepositoryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public SourceDocumentRepositoryValidationResult(
        IEnumerable<SourceDocumentRepositoryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
