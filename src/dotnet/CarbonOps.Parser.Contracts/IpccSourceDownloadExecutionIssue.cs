namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDownloadExecutionIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
