namespace CarbonOps.Parser.Contracts;

public sealed record ParserExecutionBatch
{
    public IReadOnlyList<ParserExecutionRequest> Requests { get; }

    public int RequestCount => Requests.Count;

    public ParserExecutionBatch(IEnumerable<ParserExecutionRequest> requests)
    {
        Requests = Array.AsReadOnly(requests.ToArray());
    }
}
