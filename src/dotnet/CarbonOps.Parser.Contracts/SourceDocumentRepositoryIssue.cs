namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentRepositoryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
