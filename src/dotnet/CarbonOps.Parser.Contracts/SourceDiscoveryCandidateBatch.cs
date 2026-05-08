namespace CarbonOps.Parser.Contracts;

public sealed record SourceDiscoveryCandidateBatch
{
    public IReadOnlyList<SourceDiscoveryCandidate> Candidates { get; }

    public int CandidateCount => Candidates.Count;

    public SourceDiscoveryCandidateBatch(IEnumerable<SourceDiscoveryCandidate> candidates)
    {
        Candidates = Array.AsReadOnly(candidates.ToArray());
    }
}
