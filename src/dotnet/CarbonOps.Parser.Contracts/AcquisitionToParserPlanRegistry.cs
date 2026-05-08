namespace CarbonOps.Parser.Contracts;

public static class AcquisitionToParserPlanRegistry
{
    public static AcquisitionToParserPlanBatch CreateDefaultPlanBatch()
    {
        return CreatePlanBatch(SourceAcquisitionRunRegistry.CreateDefaultRunResults());
    }

    public static AcquisitionToParserPlanBatch CreatePlanBatch(IEnumerable<SourceAcquisitionRunResult> acquisitionResults)
    {
        return new AcquisitionToParserPlanBatch(acquisitionResults.Select(CreatePlan));
    }

    public static AcquisitionToParserPlan CreatePlan(SourceAcquisitionRunResult acquisitionResult)
    {
        if (!ParserAdapterDescriptorRegistry.TryGetBySourceFamily(acquisitionResult.SourceFamily, out var descriptor) ||
            descriptor is null)
        {
            throw new InvalidOperationException(
                $"Parser adapter descriptor is missing for source family '{acquisitionResult.SourceFamily.ToWireName()}'.");
        }

        var bridgeBatch = SourceArtifactParserInputBridgeRegistry.CreateBridgeBatch(acquisitionResult.Artifacts);
        var parserRunRequest = new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            bridgeBatch.Bridges.Select(bridge => bridge.ParserInputArtifact),
            runId: acquisitionResult.RunId is null
                ? $"{descriptor.SourceFamily.ToWireName()}_parser_adapter_run"
                : $"{acquisitionResult.RunId}_parser_adapter_run",
            correlationId: acquisitionResult.CorrelationId,
            requestedReportingYear: acquisitionResult.ReportingYear);

        return AcquisitionToParserPlan.FromAcquisitionResult(acquisitionResult, bridgeBatch, parserRunRequest);
    }
}
