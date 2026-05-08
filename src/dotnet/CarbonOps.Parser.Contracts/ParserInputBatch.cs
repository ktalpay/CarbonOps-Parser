namespace CarbonOps.Parser.Contracts;

public sealed record ParserInputBatch
{
    public IReadOnlyList<ParserInputDocument> Documents { get; }

    public int DocumentCount => Documents.Count;

    public ParserInputBatch(IEnumerable<ParserInputDocument> documents)
    {
        Documents = Array.AsReadOnly(documents.ToArray());
    }
}
