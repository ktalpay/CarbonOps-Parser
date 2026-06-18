namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDiscoveryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
