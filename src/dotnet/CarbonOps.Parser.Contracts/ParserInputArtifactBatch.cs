namespace CarbonOps.Parser.Contracts;

public sealed record ParserInputArtifactBatch
{
    public IReadOnlyList<ParserInputArtifact> Artifacts { get; }

    public int ArtifactCount => Artifacts.Count;

    public ParserInputArtifactBatch(IEnumerable<ParserInputArtifact> artifacts)
    {
        Artifacts = Array.AsReadOnly(artifacts.ToArray());
    }
}
