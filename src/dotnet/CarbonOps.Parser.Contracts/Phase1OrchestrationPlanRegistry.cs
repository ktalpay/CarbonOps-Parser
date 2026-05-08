namespace CarbonOps.Parser.Contracts;

public static class Phase1OrchestrationPlanRegistry
{
    public static Phase1OrchestrationPlanBatch CreateDefaultPlanBatch()
    {
        return CreatePlanBatch(
            SourceAcquisitionRunRegistry.CreateDefaultRunRequests(),
            SourceAcquisitionRunRegistry.CreateDefaultRunResults());
    }

    public static Phase1OrchestrationPlanBatch CreatePlanBatch(
        IEnumerable<SourceAcquisitionRunRequest> acquisitionRequests,
        IEnumerable<SourceAcquisitionRunResult> acquisitionResults)
    {
        var requestsBySourceFamily = acquisitionRequests.ToDictionary(request => request.SourceFamily);

        return new Phase1OrchestrationPlanBatch(acquisitionResults.Select(result =>
        {
            if (!requestsBySourceFamily.TryGetValue(result.SourceFamily, out var request))
            {
                throw new InvalidOperationException(
                    $"Source acquisition run request is missing for source family '{result.SourceFamily.ToWireName()}'.");
            }

            return CreatePlan(request, result);
        }));
    }

    public static Phase1OrchestrationPlan CreatePlan(
        SourceAcquisitionRunRequest acquisitionRequest,
        SourceAcquisitionRunResult acquisitionResult)
    {
        var acquisitionToParserPlan = AcquisitionToParserPlanRegistry.CreatePlan(acquisitionResult);
        var dryRunPlans = acquisitionToParserPlan.ParserRunRequests
            .Select(ParserDryRunBoundaryPlanner.CreatePlan)
            .ToArray();
        var dryRunResults = dryRunPlans
            .Select(ParserDryRunBoundaryPlanner.CreateResult)
            .ToArray();
        var planIssues = dryRunPlans
            .SelectMany(plan => plan.ValidationIssues)
            .ToArray();
        var status = DetermineStatus(acquisitionToParserPlan, dryRunPlans);

        return new Phase1OrchestrationPlan(
            acquisitionResult.SourceFamily,
            acquisitionResult.SourceKey,
            acquisitionRequest,
            acquisitionResult,
            acquisitionToParserPlan,
            acquisitionToParserPlan.ParserRunRequests,
            dryRunPlans,
            dryRunResults,
            planIssues,
            status,
            orchestrationPlanId: $"{acquisitionResult.SourceKey}_phase1_orchestration_plan",
            correlationId: acquisitionResult.CorrelationId ?? acquisitionRequest.CorrelationId);
    }

    private static Phase1OrchestrationPlanStatus DetermineStatus(
        AcquisitionToParserPlan acquisitionToParserPlan,
        IReadOnlyList<ParserDryRunBoundaryPlan> dryRunPlans)
    {
        if (acquisitionToParserPlan.Status != AcquisitionToParserPlanStatus.Planned ||
            dryRunPlans.Any(plan => plan.Status == ParserDryRunStatus.InvalidRequest))
        {
            return Phase1OrchestrationPlanStatus.InvalidMetadata;
        }

        if (dryRunPlans.Any(plan => !plan.IsExecutionImplemented))
        {
            return Phase1OrchestrationPlanStatus.ExecutionNotImplemented;
        }

        return Phase1OrchestrationPlanStatus.Planned;
    }
}
