namespace CarbonOps.Parser.Contracts;

public sealed record AcquisitionToParserPlanBatch
{
    public IReadOnlyList<AcquisitionToParserPlan> Plans { get; }

    public int PlanCount => Plans.Count;

    public AcquisitionToParserPlanBatch(IEnumerable<AcquisitionToParserPlan> plans)
    {
        Plans = Array.AsReadOnly(plans.ToArray());
    }
}
