namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentPersistenceRecord(
    SourceFamily SourceFamily,
    string SourceDocumentReference,
    string SourceChecksumAlgorithm,
    string SourceChecksumValue,
    bool IsDryRunChecksum);
