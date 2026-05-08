namespace CarbonOps.Parser.Contracts;

public sealed record ParserNormalizedOutputBatch
{
    public IReadOnlyList<ParserNormalizedOutputRow> Rows { get; }

    public int RowCount => Rows.Count;

    public ParserNormalizedOutputBatch(IEnumerable<ParserNormalizedOutputRow> rows)
    {
        Rows = Array.AsReadOnly(rows.ToArray());
    }
}
