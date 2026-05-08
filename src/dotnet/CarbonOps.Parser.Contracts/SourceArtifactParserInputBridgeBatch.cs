namespace CarbonOps.Parser.Contracts;

public sealed record SourceArtifactParserInputBridgeBatch
{
    public IReadOnlyList<SourceArtifactParserInputBridge> Bridges { get; }

    public int BridgeCount => Bridges.Count;

    public SourceArtifactParserInputBridgeBatch(IEnumerable<SourceArtifactParserInputBridge> bridges)
    {
        Bridges = Array.AsReadOnly(bridges.ToArray());
    }
}
