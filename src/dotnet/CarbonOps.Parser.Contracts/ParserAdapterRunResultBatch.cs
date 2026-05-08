namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterRunResultBatch
{
    public IReadOnlyList<ParserAdapterRunResult> Results { get; }

    public int ResultCount => Results.Count;

    public ParserAdapterRunResultBatch(IEnumerable<ParserAdapterRunResult> results)
    {
        Results = Array.AsReadOnly(results.ToArray());
    }
}
