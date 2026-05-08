namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentManifestEntry(
    SourceFamily SourceFamily,
    string SourceName,
    string SourceReference,
    SourceDocumentChecksum Checksum);
