namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentMetadata(
    SourceFamily SourceFamily,
    SourceDocumentStatus SourceDocumentStatus,
    string SourceName,
    string? SourceUrl,
    int? ReportingYear,
    string? Checksum);
