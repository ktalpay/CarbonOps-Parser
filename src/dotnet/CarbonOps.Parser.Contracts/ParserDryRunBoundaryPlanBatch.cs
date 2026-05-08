namespace CarbonOps.Parser.Contracts;

public sealed record ParserDryRunBoundaryPlanBatch
{
    public IReadOnlyList<ParserDryRunBoundaryPlan> Plans { get; }

    public int PlanCount => Plans.Count;

    public ParserDryRunBoundaryPlanBatch(IEnumerable<ParserDryRunBoundaryPlan> plans)
    {
        Plans = Array.AsReadOnly(plans.ToArray());
    }
}
