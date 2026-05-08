namespace CarbonOps.Parser.Contracts;

public static class Phase1OrchestrationExecutorBoundary
{
    public static Phase1OrchestrationExecutorResultBatch CreateDefaultResultBatch()
    {
        return CreateResultBatch(Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans);
    }

    public static Phase1OrchestrationExecutorResultBatch CreateResultBatch(
        IEnumerable<Phase1OrchestrationPlan> plans)
    {
        return new Phase1OrchestrationExecutorResultBatch(plans.Select(plan => CreateResult(CreateRequest(plan))));
    }

    public static Phase1OrchestrationExecutorRequest CreateRequest(Phase1OrchestrationPlan plan)
    {
        return new Phase1OrchestrationExecutorRequest(
            plan.SourceFamily,
            plan.SourceKey,
            plan,
            executorRequestId: $"{plan.SourceKey}_phase1_executor_request",
            correlationId: plan.CorrelationId);
    }

    public static Phase1OrchestrationExecutorResult CreateResult(Phase1OrchestrationExecutorRequest request)
    {
        var validationResult = request.Validate();
        var status = DetermineStatus(request.Plan, validationResult);
        var readinessReason = DetermineReadinessReason(request.Plan, validationResult, status);

        return new Phase1OrchestrationExecutorResult(
            request.SourceFamily,
            request.SourceKey,
            request.Plan,
            status,
            readinessReason,
            request.Plan.PlanIssues,
            request.ExecutorRequestId,
            request.CorrelationId);
    }

    private static Phase1OrchestrationExecutorStatus DetermineStatus(
        Phase1OrchestrationPlan plan,
        ContractValidationResult validationResult)
    {
        if (!validationResult.IsValid)
        {
            return Phase1OrchestrationExecutorStatus.InvalidPlan;
        }

        if (plan.Status == Phase1OrchestrationPlanStatus.InvalidMetadata ||
            plan.StructurallyExecutableDryRunCount != plan.DryRunPlanCount)
        {
            return Phase1OrchestrationExecutorStatus.NotExecutable;
        }

        if (plan.ExecutionImplementedDryRunCount != plan.DryRunPlanCount)
        {
            return Phase1OrchestrationExecutorStatus.NotImplemented;
        }

        return Phase1OrchestrationExecutorStatus.Planned;
    }

    private static string DetermineReadinessReason(
        Phase1OrchestrationPlan plan,
        ContractValidationResult validationResult,
        Phase1OrchestrationExecutorStatus status) =>
        status switch
        {
            Phase1OrchestrationExecutorStatus.Planned =>
                "Phase 1 orchestration metadata is structurally ready.",
            Phase1OrchestrationExecutorStatus.NotExecutable =>
                "Phase 1 orchestration metadata is not structurally executable.",
            Phase1OrchestrationExecutorStatus.NotImplemented =>
                "Phase 1 orchestration execution is not implemented; boundary is metadata-only.",
            Phase1OrchestrationExecutorStatus.InvalidPlan =>
                $"Phase 1 orchestration plan is invalid: {validationResult.Errors.FirstOrDefault() ?? "metadata validation failed"}.",
            _ =>
                $"Phase 1 orchestration plan status '{plan.Status}' is not executable.",
        };
}
