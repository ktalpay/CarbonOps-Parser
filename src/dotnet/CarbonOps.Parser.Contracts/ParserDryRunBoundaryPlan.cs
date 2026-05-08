namespace CarbonOps.Parser.Contracts;

public sealed record ParserDryRunBoundaryPlan
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public ParserAdapterRunRequest Request { get; }

    public ParserDryRunStatus Status { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public bool IsStructurallyExecutable { get; }

    public IReadOnlyList<ParserValidationIssue> ValidationIssues { get; }

    public int ArtifactCount => Request.ArtifactCount;

    public int IssueCount => ValidationIssues.Count;

    public ParserDryRunBoundaryPlan(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        ParserAdapterRunRequest request,
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
        Status = status;
        Readiness = readiness;
        IsExecutionImplemented = isExecutionImplemented;
        IsStructurallyExecutable = isStructurallyExecutable;
        ValidationIssues = Array.AsReadOnly((validationIssues ?? []).ToArray());
    }
}
