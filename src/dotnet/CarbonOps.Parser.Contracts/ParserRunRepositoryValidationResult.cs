namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunRepositoryValidationResult
{
    public IReadOnlyList<ParserRunRepositoryIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public ParserRunRepositoryValidationResult(
        IEnumerable<ParserRunRepositoryIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
