namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDiscoveryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
