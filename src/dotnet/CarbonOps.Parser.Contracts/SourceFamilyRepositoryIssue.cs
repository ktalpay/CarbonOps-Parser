namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyRepositoryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
