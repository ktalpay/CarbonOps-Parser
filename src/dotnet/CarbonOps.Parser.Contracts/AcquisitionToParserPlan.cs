namespace CarbonOps.Parser.Contracts;

public sealed record AcquisitionToParserPlan
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public string? AcquisitionRunId { get; }

    public AcquisitionToParserPlanStatus Status { get; }

    public SourceAcquisitionRunResult AcquisitionResult { get; }

    public IReadOnlyList<SourceArtifactParserInputBridge> Bridges { get; }

    public IReadOnlyList<ParserAdapterRunRequest> ParserRunRequests { get; }

    public int DownloadedArtifactCount => AcquisitionResult.ArtifactCount;

    public int ParserInputArtifactCount => Bridges.Count;

    public int ParserRunRequestCount => ParserRunRequests.Count;

    public AcquisitionToParserPlan(
        SourceFamily sourceFamily,
        string sourceKey,
        SourceAcquisitionRunResult acquisitionResult,
        IEnumerable<SourceArtifactParserInputBridge> bridges,
        IEnumerable<ParserAdapterRunRequest> parserRunRequests,
        AcquisitionToParserPlanStatus status = AcquisitionToParserPlanStatus.Planned,
        string? acquisitionRunId = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        AcquisitionResult = acquisitionResult;
        Bridges = Array.AsReadOnly(bridges.ToArray());
        ParserRunRequests = Array.AsReadOnly(parserRunRequests.ToArray());
        Status = status;
        AcquisitionRunId = acquisitionRunId;
    }

    internal static AcquisitionToParserPlan FromAcquisitionResult(
        SourceAcquisitionRunResult acquisitionResult,
        SourceArtifactParserInputBridgeBatch bridgeBatch,
        ParserAdapterRunRequest parserRunRequest)
    {
        return new AcquisitionToParserPlan(
            acquisitionResult.SourceFamily,
            acquisitionResult.SourceKey,
            acquisitionResult,
            bridgeBatch.Bridges,
            [parserRunRequest],
            acquisitionResult.ArtifactCount == 0
                ? AcquisitionToParserPlanStatus.NoSourceArtifacts
                : AcquisitionToParserPlanStatus.Planned,
            acquisitionResult.RunId);
    }
}
