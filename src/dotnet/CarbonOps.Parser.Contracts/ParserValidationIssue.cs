namespace CarbonOps.Parser.Contracts;

public sealed record ParserValidationIssue
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public ParserValidationIssueSeverity Severity { get; }

    public string Code { get; }

    public string Message { get; }

    public string? ArtifactReference { get; }

    public string? RowIdentifier { get; }

    public int? SourceRowNumber { get; }

    public string? FieldKey { get; }

    public IReadOnlyList<ParserValidationIssueContext> Context { get; }

    public ParserValidationIssue(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        ParserValidationIssueSeverity severity,
        string code,
        string message,
        string? artifactReference = null,
        string? rowIdentifier = null,
        int? sourceRowNumber = null,
        string? fieldKey = null,
        IEnumerable<ParserValidationIssueContext>? context = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        Severity = severity;
        Code = code;
        Message = message;
        ArtifactReference = artifactReference;
        RowIdentifier = rowIdentifier;
        SourceRowNumber = sourceRowNumber;
        FieldKey = fieldKey;
        Context = Array.AsReadOnly((context ?? []).ToArray());
    }

    internal static ParserValidationIssue FromNormalizedRow(ParserNormalizedOutputRow row) =>
        new(
            row.SourceFamily,
            row.SourceKey,
            row.ParserKey,
            ParserValidationIssueSeverity.Info,
            "PARSER_VALIDATION_DRY_RUN",
            "Metadata-only parser validation diagnostic.",
            row.ArtifactReference,
            row.RowIdentifier,
            row.SourceRowNumber,
            fieldKey: null,
            [
                new ParserValidationIssueContext("source_key", row.SourceKey),
                new ParserValidationIssueContext("parser_key", row.ParserKey.Value),
                new ParserValidationIssueContext("row_identifier", row.RowIdentifier),
            ]);
}
