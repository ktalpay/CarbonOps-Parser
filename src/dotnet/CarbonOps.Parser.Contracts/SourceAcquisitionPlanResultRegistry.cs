namespace CarbonOps.Parser.Contracts;

public static class SourceAcquisitionPlanResultRegistry
{
    public static SourceAcquisitionPlanResult CreateDefaultDryRunResult() =>
        CreateDryRunResult(SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan());

    public static SourceAcquisitionPlanResult CreateDryRunResult(SourceAcquisitionPlan plan) =>
        new(
            plan.Mode,
            plan.Requests.Select(request => new SourceAcquisitionRequestResult(
                request,
                SourceAcquisitionRequestResultStatus.Planned)));
}
