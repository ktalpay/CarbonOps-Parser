namespace CarbonOps.Parser.Contracts;

public sealed record ParserDryRunBoundaryResultBatch
{
    public IReadOnlyList<ParserDryRunBoundaryResult> Results { get; }

    public int ResultCount => Results.Count;

    public ParserDryRunBoundaryResultBatch(IEnumerable<ParserDryRunBoundaryResult> results)
    {
        Results = Array.AsReadOnly(results.ToArray());
    }
}
