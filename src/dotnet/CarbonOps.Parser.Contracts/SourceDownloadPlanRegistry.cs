namespace CarbonOps.Parser.Contracts;

public static class SourceDownloadPlanRegistry
{
    public static SourceDownloadPlan CreateDefaultDryRunPlan() =>
        CreateDryRunPlan(SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult());

    public static SourceDownloadPlan CreateDryRunPlan(SourceAcquisitionPlanResult acquisitionResult) =>
        new(
            acquisitionResult.Mode,
            acquisitionResult.Results.Select(result => new SourceDownloadRequest(
                result.Request.SourceFamily,
                result.Request.SourceName,
                result.Request.SourceReference)));
}
