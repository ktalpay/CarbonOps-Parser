namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentManifest
{
    public IReadOnlyList<SourceDocumentManifestEntry> Entries { get; }

    public int EntryCount => Entries.Count;

    public SourceDocumentManifest(IEnumerable<SourceDocumentManifestEntry> entries)
    {
        Entries = Array.AsReadOnly(entries.ToArray());
    }
}
