namespace CarbonOps.Parser.Contracts;

public sealed record SourceDownloadArtifactBatch
{
    public IReadOnlyList<SourceDownloadArtifact> Artifacts { get; }

    public int ArtifactCount => Artifacts.Count;

    public SourceDownloadArtifactBatch(IEnumerable<SourceDownloadArtifact> artifacts)
    {
        Artifacts = Array.AsReadOnly(artifacts.ToArray());
    }
}
