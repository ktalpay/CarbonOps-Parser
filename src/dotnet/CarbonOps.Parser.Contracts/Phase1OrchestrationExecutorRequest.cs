namespace CarbonOps.Parser.Contracts;

public sealed record Phase1OrchestrationExecutorRequest
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public Phase1OrchestrationPlan Plan { get; }

    public string? ExecutorRequestId { get; }

    public string? CorrelationId { get; }

    public string? OrchestrationPlanId => Plan.OrchestrationPlanId;

    public Phase1OrchestrationExecutorRequest(
        SourceFamily sourceFamily,
        string sourceKey,
        Phase1OrchestrationPlan plan,
        string? executorRequestId = null,
        string? correlationId = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        Plan = plan;
        ExecutorRequestId = executorRequestId;
        CorrelationId = correlationId;
    }
}
