namespace CarbonOps.Parser.Contracts;

public sealed record ParsedFactorPersistenceIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
