namespace CarbonOps.Parser.Contracts;

public static class SourceDiscoveryCandidateRegistry
{
    public static SourceDiscoveryCandidateBatch CreateDefaultCandidateBatch()
    {
        var descriptorsBySourceFamily = ParserAdapterDescriptorRegistry.Descriptors
            .ToDictionary(descriptor => descriptor.SourceFamily);

        return new SourceDiscoveryCandidateBatch(SourceDiscoveryRegistry.CreateDefaultDiscoveryResult()
            .Documents
            .Select(document =>
            {
                if (!descriptorsBySourceFamily.TryGetValue(document.SourceFamily, out var descriptor))
                {
                    throw new InvalidOperationException(
                        $"Parser adapter descriptor is missing for source family '{document.SourceFamily.ToWireName()}'.");
                }

                return SourceDiscoveryCandidate.FromDocumentAndDescriptor(document, descriptor);
            }));
    }
}
