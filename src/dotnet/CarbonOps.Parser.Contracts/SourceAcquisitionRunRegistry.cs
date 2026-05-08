namespace CarbonOps.Parser.Contracts;

public static class SourceAcquisitionRunRegistry
{
    public static IReadOnlyList<SourceAcquisitionRunRequest> CreateDefaultRunRequests()
    {
        var candidatesBySourceFamily = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch()
            .Candidates
            .GroupBy(candidate => candidate.SourceFamily)
            .ToDictionary(group => group.Key, group => group.AsEnumerable());

        return Array.AsReadOnly(ParserAdapterDescriptorRegistry.Descriptors
            .Select(descriptor =>
            {
                if (!candidatesBySourceFamily.TryGetValue(descriptor.SourceFamily, out var candidates))
                {
                    throw new InvalidOperationException(
                        $"Source discovery candidate is missing for source family '{descriptor.SourceFamily.ToWireName()}'.");
                }

                return SourceAcquisitionRunRequest.FromCandidates(descriptor.SourceFamily, candidates);
            })
            .ToArray());
    }

    public static IReadOnlyList<SourceAcquisitionRunResult> CreateDefaultRunResults()
    {
        var candidatesBySourceFamily = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch()
            .Candidates
            .GroupBy(candidate => candidate.SourceFamily)
            .ToDictionary(group => group.Key, group => group.AsEnumerable());
        var artifactsBySourceFamily = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch()
            .Artifacts
            .GroupBy(artifact => artifact.SourceFamily)
            .ToDictionary(group => group.Key, group => group.AsEnumerable());

        return Array.AsReadOnly(ParserAdapterDescriptorRegistry.Descriptors
            .Select(descriptor =>
            {
                if (!candidatesBySourceFamily.TryGetValue(descriptor.SourceFamily, out var candidates))
                {
                    throw new InvalidOperationException(
                        $"Source discovery candidate is missing for source family '{descriptor.SourceFamily.ToWireName()}'.");
                }

                if (!artifactsBySourceFamily.TryGetValue(descriptor.SourceFamily, out var artifacts))
                {
                    throw new InvalidOperationException(
                        $"Source download artifact is missing for source family '{descriptor.SourceFamily.ToWireName()}'.");
                }

                return SourceAcquisitionRunResult.FromCandidatesAndArtifacts(
                    descriptor.SourceFamily,
                    candidates,
                    artifacts);
            })
            .ToArray());
    }
}
