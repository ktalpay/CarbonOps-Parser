namespace CarbonOps.Parser.Contracts;

public sealed record ParserInputDocument(
    SourceFamily SourceFamily,
    string SourceDocumentReference,
    ParserSourceFormat SourceFormat,
    string ContentType,
    string FormatHint,
    string SourceChecksumAlgorithm,
    string SourceChecksumValue,
    bool IsDryRunChecksum);
