namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeConfigGateIssue(
    string Code,
    string Message,
    string? FieldName = null,
    string Severity = "warning");
