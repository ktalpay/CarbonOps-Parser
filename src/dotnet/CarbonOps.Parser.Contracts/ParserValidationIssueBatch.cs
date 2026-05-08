namespace CarbonOps.Parser.Contracts;

public sealed record ParserValidationIssueBatch
{
    public IReadOnlyList<ParserValidationIssue> Issues { get; }

    public int IssueCount => Issues.Count;

    public ParserValidationIssueBatch(IEnumerable<ParserValidationIssue> issues)
    {
        Issues = Array.AsReadOnly(issues.ToArray());
    }
}
