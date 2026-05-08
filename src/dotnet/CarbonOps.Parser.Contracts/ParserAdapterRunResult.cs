namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterRunResult
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public ParserRunStatus Status { get; }

    public IReadOnlyList<string> ArtifactReferences { get; }

    public IReadOnlyList<ParserNormalizedOutputRow> Rows { get; }

    public IReadOnlyList<ParserValidationIssue> ValidationIssues { get; }

    public string? RunId { get; }

    public string? CorrelationId { get; }

    public int? ReportingYear { get; }

    public int ArtifactCount => ArtifactReferences.Count;

    public int RowCount => Rows.Count;

    public int IssueCount => ValidationIssues.Count;

    public ParserAdapterRunResult(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        ParserRunStatus status,
        IEnumerable<string> artifactReferences,
        IEnumerable<ParserNormalizedOutputRow> rows,
        IEnumerable<ParserValidationIssue> validationIssues,
        string? runId = null,
        string? correlationId = null,
        int? reportingYear = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        Status = status;
        ArtifactReferences = Array.AsReadOnly(artifactReferences.ToArray());
        Rows = Array.AsReadOnly(rows.ToArray());
        ValidationIssues = Array.AsReadOnly(validationIssues.ToArray());
        RunId = runId;
        CorrelationId = correlationId;
        ReportingYear = reportingYear;
    }

    internal static ParserAdapterRunResult FromRequestRowsAndIssues(
        ParserAdapterRunRequest request,
        IEnumerable<ParserNormalizedOutputRow> rows,
        IEnumerable<ParserValidationIssue> validationIssues) =>
        new(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            ParserRunStatus.Pending,
            request.Artifacts.Select(artifact => artifact.ArtifactReference),
            rows,
            validationIssues,
            request.RunId,
            request.CorrelationId,
            request.RequestedReportingYear);
}
