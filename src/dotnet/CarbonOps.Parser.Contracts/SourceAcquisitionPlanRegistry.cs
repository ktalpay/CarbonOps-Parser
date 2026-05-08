namespace CarbonOps.Parser.Contracts;

public static class SourceAcquisitionPlanRegistry
{
    public static SourceAcquisitionPlan CreateDefaultDryRunPlan()
    {
        var discoveryResult = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var requests = discoveryResult.Documents.Select(document => new SourceAcquisitionRequest(
            document.SourceFamily,
            document.SourceName,
            document.SourceReference,
            SourceAcquisitionMode.DryRun));

        return new SourceAcquisitionPlan(SourceAcquisitionMode.DryRun, requests);
    }
}
