namespace CarbonOps.Parser.Contracts;

public static class SourceArtifactParserInputBridgeRegistry
{
    public static SourceArtifactParserInputBridgeBatch CreateDefaultBridgeBatch()
    {
        return CreateBridgeBatch(SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts);
    }

    public static SourceArtifactParserInputBridgeBatch CreateBridgeBatch(IEnumerable<SourceDownloadArtifact> sourceArtifacts)
    {
        var descriptorsBySourceFamily = ParserAdapterDescriptorRegistry.Descriptors
            .ToDictionary(descriptor => descriptor.SourceFamily);

        return new SourceArtifactParserInputBridgeBatch(sourceArtifacts.Select(sourceArtifact =>
        {
            if (!descriptorsBySourceFamily.TryGetValue(sourceArtifact.SourceFamily, out var descriptor))
            {
                throw new InvalidOperationException(
                    $"Parser adapter descriptor is missing for source family '{sourceArtifact.SourceFamily.ToWireName()}'.");
            }

            return SourceArtifactParserInputBridge.FromSourceArtifact(sourceArtifact, descriptor);
        }));
    }

    public static SourceArtifactParserInputBridge CreateBridge(SourceDownloadArtifact sourceArtifact)
    {
        if (!ParserAdapterDescriptorRegistry.TryGetBySourceFamily(sourceArtifact.SourceFamily, out var descriptor) ||
            descriptor is null)
        {
            throw new InvalidOperationException(
                $"Parser adapter descriptor is missing for source family '{sourceArtifact.SourceFamily.ToWireName()}'.");
        }

        return SourceArtifactParserInputBridge.FromSourceArtifact(sourceArtifact, descriptor);
    }
}
