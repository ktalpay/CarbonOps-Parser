namespace CarbonOps.Parser.Contracts;

public sealed record Phase1OrchestrationPlanBatch
{
    public IReadOnlyList<Phase1OrchestrationPlan> Plans { get; }

    public int PlanCount => Plans.Count;

    public Phase1OrchestrationPlanBatch(IEnumerable<Phase1OrchestrationPlan> plans)
    {
        Plans = Array.AsReadOnly(plans.ToArray());
    }
}
