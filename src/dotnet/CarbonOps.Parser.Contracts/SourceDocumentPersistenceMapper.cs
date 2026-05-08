namespace CarbonOps.Parser.Contracts;

public static class SourceDocumentPersistenceMapper
{
    public static SourceDocumentPersistenceMapping MapDefaultDryRunManifest() =>
        MapManifest(SourceDocumentManifestRegistry.CreateDefaultDryRunManifest());

    public static SourceDocumentPersistenceMapping MapManifest(SourceDocumentManifest manifest) =>
        new(manifest.Entries.Select(MapEntry));

    private static SourceDocumentPersistenceRecord MapEntry(SourceDocumentManifestEntry entry) =>
        new(
            entry.SourceFamily,
            entry.SourceReference,
            entry.Checksum.Algorithm,
            entry.Checksum.Value,
            entry.Checksum.IsDryRunPlaceholder);
}
