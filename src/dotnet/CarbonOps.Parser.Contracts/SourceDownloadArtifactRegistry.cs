namespace CarbonOps.Parser.Contracts;

public static class SourceDownloadArtifactRegistry
{
    public static SourceDownloadArtifactBatch CreateDefaultArtifactBatch() =>
        new(SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch()
            .Candidates
            .Select(SourceDownloadArtifact.FromDiscoveryCandidate));
}
