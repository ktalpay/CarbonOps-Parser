namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterRunRequestBatch
{
    public IReadOnlyList<ParserAdapterRunRequest> Requests { get; }

    public int RequestCount => Requests.Count;

    public ParserAdapterRunRequestBatch(IEnumerable<ParserAdapterRunRequest> requests)
    {
        Requests = Array.AsReadOnly(requests.ToArray());
    }
}
