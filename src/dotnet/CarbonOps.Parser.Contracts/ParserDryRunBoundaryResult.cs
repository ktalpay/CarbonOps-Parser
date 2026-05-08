namespace CarbonOps.Parser.Contracts;

public sealed record ParserDryRunBoundaryResult
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public ParserAdapterRunRequest Request { get; }

    public ParserAdapterRunResult RunResult { get; }

    public ParserDryRunStatus Status { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public bool IsStructurallyExecutable { get; }

    public IReadOnlyList<ParserValidationIssue> ValidationIssues { get; }

    public int ArtifactCount => Request.ArtifactCount;

    public int RowCount => RunResult.RowCount;

    public int IssueCount => ValidationIssues.Count;

    public ParserDryRunBoundaryResult(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        ParserAdapterRunRequest request,
        ParserAdapterRunResult runResult,
        ParserDryRunStatus status,
        ParserAdapterReadiness readiness,
        bool isExecutionImplemented,
        bool isStructurallyExecutable,
        IEnumerable<ParserValidationIssue>? validationIssues = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        Request = request;
        RunResult = runResult;
        Status = status;
        Readiness = readiness;
        IsExecutionImplemented = isExecutionImplemented;
        IsStructurallyExecutable = isStructurallyExecutable;
        ValidationIssues = Array.AsReadOnly((validationIssues ?? []).ToArray());
    }
}
