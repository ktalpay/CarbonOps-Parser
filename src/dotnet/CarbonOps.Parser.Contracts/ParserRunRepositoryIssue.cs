namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunRepositoryIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");
