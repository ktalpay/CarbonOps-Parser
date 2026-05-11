namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDownloadExecutionIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
