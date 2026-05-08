namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunSummary(
    SourceFamily SourceFamily,
    ParserRunStatus ParserRunStatus,
    string SourceDocumentId,
    int TotalRows,
    int AcceptedRows,
    int RejectedRows);
