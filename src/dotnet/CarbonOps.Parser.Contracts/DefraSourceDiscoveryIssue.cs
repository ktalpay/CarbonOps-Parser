namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDiscoveryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
