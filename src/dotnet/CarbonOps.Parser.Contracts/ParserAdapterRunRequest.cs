namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterRunRequest
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public IReadOnlyList<ParserInputArtifact> Artifacts { get; }

    public string? RunId { get; }

    public string? CorrelationId { get; }

    public int? RequestedReportingYear { get; }

    public int ArtifactCount => Artifacts.Count;

    public ParserAdapterRunRequest(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        IEnumerable<ParserInputArtifact> artifacts,
        string? runId = null,
        string? correlationId = null,
        int? requestedReportingYear = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        Artifacts = Array.AsReadOnly(artifacts.ToArray());
        RunId = runId;
        CorrelationId = correlationId;
        RequestedReportingYear = requestedReportingYear;
    }

    internal static ParserAdapterRunRequest FromDescriptorAndArtifacts(
        IParserAdapterDescriptor descriptor,
        IEnumerable<ParserInputArtifact> artifacts) =>
        new(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            artifacts);
}
