namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDownloadExecutionIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
