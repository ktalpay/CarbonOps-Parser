namespace CarbonOps.Parser.Contracts;

public static class ParserNormalizedOutputRegistry
{
    public static ParserNormalizedOutputBatch CreateDefaultDryRunBatch() =>
        new(ParserInputArtifactRegistry.CreateDefaultDryRunBatch()
            .Artifacts
            .Select(ParserNormalizedOutputRow.FromArtifact));
}
