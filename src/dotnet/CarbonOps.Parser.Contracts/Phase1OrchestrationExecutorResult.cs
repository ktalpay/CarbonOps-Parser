namespace CarbonOps.Parser.Contracts;

public sealed record Phase1OrchestrationExecutorResult
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public Phase1OrchestrationPlan Plan { get; }

    public Phase1OrchestrationExecutorStatus Status { get; }

    public string ReadinessReason { get; }

    public string? ExecutorRequestId { get; }

    public string? CorrelationId { get; }

    public string? OrchestrationPlanId => Plan.OrchestrationPlanId;

    public IReadOnlyList<ParserValidationIssue> PlanIssues { get; }

    public int SourceCandidateCount => Plan.SourceCandidateCount;

    public int DownloadedArtifactCount => Plan.DownloadedArtifactCount;

    public int ParserInputArtifactCount => Plan.ParserInputArtifactCount;

    public int ParserRunRequestCount => Plan.ParserRunRequestCount;

    public int DryRunPlanCount => Plan.DryRunPlanCount;

    public int DryRunResultCount => Plan.DryRunResultCount;

    public int StructurallyExecutableDryRunCount => Plan.StructurallyExecutableDryRunCount;

    public int ExecutionImplementedDryRunCount => Plan.ExecutionImplementedDryRunCount;

    public int PlanIssueCount => PlanIssues.Count;

    public Phase1OrchestrationExecutorResult(
        SourceFamily sourceFamily,
        string sourceKey,
        Phase1OrchestrationPlan plan,
        Phase1OrchestrationExecutorStatus status,
        string readinessReason,
        IEnumerable<ParserValidationIssue>? planIssues = null,
        string? executorRequestId = null,
        string? correlationId = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        Plan = plan;
        Status = status;
        ReadinessReason = readinessReason;
        PlanIssues = Array.AsReadOnly((planIssues ?? []).ToArray());
        ExecutorRequestId = executorRequestId;
        CorrelationId = correlationId;
    }
}
