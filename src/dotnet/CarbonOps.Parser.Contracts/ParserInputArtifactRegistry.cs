namespace CarbonOps.Parser.Contracts;

public static class ParserInputArtifactRegistry
{
    public static ParserInputArtifactBatch CreateDefaultDryRunBatch()
    {
        var inputDocuments = ParserInputRegistry.CreateDefaultDryRunBatch()
            .Documents
            .ToDictionary(document => document.SourceFamily);

        return new ParserInputArtifactBatch(ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor =>
        {
            if (!inputDocuments.TryGetValue(descriptor.SourceFamily, out var document))
            {
                throw new InvalidOperationException(
                    $"Parser input document is missing for source family '{descriptor.SourceFamily.ToWireName()}'.");
            }

            return ParserInputArtifact.FromDescriptorAndDocument(descriptor, document);
        }));
    }
}
