namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunIssue(
    string Code,
    string Message,
    ParserRunIssueSeverity Severity,
    string? Location = null);
