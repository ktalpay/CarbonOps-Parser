namespace CarbonOps.Parser.Contracts;

public sealed record ParserSelection(
    SourceFamily SourceFamily,
    ParserKey ParserKey,
    ParserInputDocument InputDocument);
