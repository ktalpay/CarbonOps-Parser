namespace CarbonOps.Parser.Contracts;

public sealed record ParserExecutionBoundaryDescriptor(
    SourceFamily SourceFamily,
    ParserKey ParserKey,
    ParserSourceFormat SourceFormat,
    string ContentType,
    string FormatHint);
