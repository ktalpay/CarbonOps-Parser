namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunResultSet
{
    public IReadOnlyList<ParserRunResult> Results { get; }

    public int ResultCount => Results.Count;

    public ParserRunResultSet(IEnumerable<ParserRunResult> results)
    {
        Results = Array.AsReadOnly(results.ToArray());
    }
}
