namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentPersistenceMapping
{
    public IReadOnlyList<SourceDocumentPersistenceRecord> Records { get; }

    public int RecordCount => Records.Count;

    public SourceDocumentPersistenceMapping(IEnumerable<SourceDocumentPersistenceRecord> records)
    {
        Records = Array.AsReadOnly(records.ToArray());
    }
}
