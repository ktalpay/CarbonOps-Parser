namespace CarbonOps.Parser.Contracts;

public sealed record ParserSelectionBatch
{
    public IReadOnlyList<ParserSelection> Selections { get; }

    public int SelectionCount => Selections.Count;

    public ParserSelectionBatch(IEnumerable<ParserSelection> selections)
    {
        Selections = Array.AsReadOnly(selections.ToArray());
    }
}
