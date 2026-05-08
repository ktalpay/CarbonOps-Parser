namespace CarbonOps.Parser.Contracts;

public sealed record Phase1OrchestrationPlan
{
    public string? OrchestrationPlanId { get; }

    public string? CorrelationId { get; }

    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public Phase1OrchestrationPlanStatus Status { get; }

    public SourceAcquisitionRunRequest AcquisitionRequest { get; }

    public SourceAcquisitionRunResult AcquisitionResult { get; }

    public AcquisitionToParserPlan AcquisitionToParserPlan { get; }

    public IReadOnlyList<ParserAdapterRunRequest> ParserRunRequests { get; }

    public IReadOnlyList<ParserDryRunBoundaryPlan> DryRunPlans { get; }

    public IReadOnlyList<ParserDryRunBoundaryResult> DryRunResults { get; }

    public IReadOnlyList<ParserValidationIssue> PlanIssues { get; }

    public int SourceCandidateCount => AcquisitionResult.CandidateCount;

    public int DownloadedArtifactCount => AcquisitionResult.ArtifactCount;

    public int ParserInputArtifactCount => AcquisitionToParserPlan.ParserInputArtifactCount;

    public int ParserRunRequestCount => ParserRunRequests.Count;

    public int DryRunPlanCount => DryRunPlans.Count;

    public int DryRunResultCount => DryRunResults.Count;

    public int StructurallyExecutableDryRunCount => DryRunPlans.Count(plan => plan.IsStructurallyExecutable);

    public int ExecutionImplementedDryRunCount => DryRunPlans.Count(plan => plan.IsExecutionImplemented);

    public int PlanIssueCount => PlanIssues.Count;

    public Phase1OrchestrationPlan(
        SourceFamily sourceFamily,
        string sourceKey,
        SourceAcquisitionRunRequest acquisitionRequest,
        SourceAcquisitionRunResult acquisitionResult,
        AcquisitionToParserPlan acquisitionToParserPlan,
        IEnumerable<ParserAdapterRunRequest> parserRunRequests,
        IEnumerable<ParserDryRunBoundaryPlan> dryRunPlans,
        IEnumerable<ParserDryRunBoundaryResult> dryRunResults,
        IEnumerable<ParserValidationIssue>? planIssues = null,
        Phase1OrchestrationPlanStatus status = Phase1OrchestrationPlanStatus.Planned,
        string? orchestrationPlanId = null,
        string? correlationId = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        AcquisitionRequest = acquisitionRequest;
        AcquisitionResult = acquisitionResult;
        AcquisitionToParserPlan = acquisitionToParserPlan;
        ParserRunRequests = Array.AsReadOnly(parserRunRequests.ToArray());
        DryRunPlans = Array.AsReadOnly(dryRunPlans.ToArray());
        DryRunResults = Array.AsReadOnly(dryRunResults.ToArray());
        PlanIssues = Array.AsReadOnly((planIssues ?? []).ToArray());
        Status = status;
        OrchestrationPlanId = orchestrationPlanId;
        CorrelationId = correlationId;
    }
}
